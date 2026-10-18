"""The export operator: objects without overrides are written directly, the others by a headless worker process
(headless_main.py). Both are driven by a modal timer, so Blender stays usable (ARCHITECTURE.md, Execution Pipelines)."""
import collections
import os
import time
import tempfile
import shutil
import traceback

import bpy

from .common import redraw_sidebars
from .nodes import cached_menu_items
from .targets import (export_file_parts, find_export_clashes, is_direct, iter_export_objects, live_collection_names,
    sync_collection_objects)
from .stl import collect_instance_arrays, export_object_stl
from .data import ensure_preset_uids, find_job, find_preset, get_job, log_to_console
from .validation import is_preset_setup_valid
from .headless import WORKER_SCRIPT, write_job_file
from .standby import TEMP_PREFIX, WorkerOutput, ensure_standby, start_process, take_standby, worker_args

# Temp folders of a crashed export are removed at startup once they are this old; a younger one may belong to an
# export running in another Blender instance.
STALE_TEMP_AGE = 24 * 3600

# Seconds of direct writing per timer poll: the UI redraws between the polls, and the timer's other work (reading the
# worker's output) is not held up by a long queue of objects.
DIRECT_SLICE = 0.05

def find_direct_object(collection_name, object_name):
    """The object a direct export entry was queued for, found the way iter_export_objects finds it; None when it is gone.
    Pointers do not survive the undo steps that can happen between two polls, names do."""
    collection = bpy.data.collections.get(collection_name)
    return collection.all_objects.get(object_name) if collection else None

class BATCH_STL_OT_cancel_export(bpy.types.Operator):
    bl_idname = "batch_stl.cancel_export"
    bl_label = "Cancel Export"
    bl_description = "Cancel the active batch export"
    preset_uid: bpy.props.StringProperty(options={'HIDDEN'})
    def execute(self, context):
        job = find_job(context.scene.session_uid, self.preset_uid)
        if job and job.is_exporting:
            job.cancel_export = True
            log_to_console(job, "[!] Export cancelled manually.")
        return {'FINISHED'}

class EXPORT_OT_batch_stl_multi(bpy.types.Operator):
    """The export button starts the worker, then writes the objects without overrides a few at a time while following the
    worker, both with a modal timer, so Blender stays usable (invoke). Called from a script,
    bpy.ops.export_scene.batch_stl_multi(preset_index=...) writes them all and waits for the worker and returns once
    every file is written, with the worker's output printed as it comes (execute). An error is reported as such: bpy.ops
    raises it."""
    bl_idname = "export_scene.batch_stl_multi"
    bl_label = "Export"
    bl_description = "Start batch STL export"
    bl_options = {"REGISTER"}
    preset_index: bpy.props.IntProperty(name="Preset Index", description="Preset to export; -1 exports the active preset", default=-1, options={'SKIP_SAVE'})
    echo = False  # print the log lines too (a scripted export, see execute)
    direct_budget = DIRECT_SLICE  # seconds of direct writing per poll; None writes everything queued at once (see execute)
    # Run state, set by _start; these are what an operator that did not start a worker or queue anything has.
    process = output = worker_dir = instance_arrays = None
    direct_queue = ()
    direct_total = direct_done = 0
    worker_done = False

    @classmethod
    def poll(cls, context): return len(context.scene.batch_stl_presets) > 0

    def invoke(self, context, event):
        result = self._start(context)
        if result == {'RUNNING_MODAL'}:
            self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
            context.window_manager.modal_handler_add(self)
        return result

    def execute(self, context):
        self.echo, self.direct_budget = True, None
        result = self._start(context)
        while result == {'RUNNING_MODAL'}:
            time.sleep(0.1)
            result = self._poll(context)
        return result

    def _log(self, job, text):
        """A line of the export log; a scripted export prints it too."""
        log_to_console(job, text)
        if self.echo: print(text, flush=True)

    def _start(self, context):
        """Check the preset, start the worker for the objects with overrides and queue the others for direct writing.
        Only the work that has to happen at the click is done here (the checks, the snapshot the worker opens, its
        start); _poll does the rest. Returns {'RUNNING_MODAL'} while the worker runs or objects are queued."""
        self._timer = self.process = self.output = self.worker_dir = self.instance_arrays = None
        self.direct_queue, self.direct_total, self.direct_done, self.worker_done = collections.deque(), 0, 0, True
        self.total_operations, self.current_op = 1, 0
        self.export_start_time = time.perf_counter()
        scene = context.scene

        preset_idx = self.preset_index if self.preset_index >= 0 else scene.batch_stl_preset_index
        if preset_idx < 0 or preset_idx >= len(scene.batch_stl_presets):
            self.report({'ERROR'}, f"No preset at index {preset_idx}")
            return {"CANCELLED"}
        scene.batch_stl_preset_index = preset_idx
        ensure_preset_uids(scene)
        preset = scene.batch_stl_presets[preset_idx]
        # Undo, reordering and scene switches invalidate pointers and indices: modal() and cleanup() find the preset
        # and its job again by these.
        self.scene_uid, self.preset_uid, self.preset_name = scene.session_uid, preset.uid, preset.name
        job = get_job(preset, create=True)

        if job.is_exporting:
            self.report({'ERROR'}, f"{preset.name} is already exporting")
            return {'CANCELLED'}
        if not scene.batch_stl_root_dir:
            self.report({'ERROR'}, "Missing Root Directory")
            return {"CANCELLED"}
        if scene.batch_stl_root_dir.startswith("//") and not bpy.data.is_saved:
            self.report({'ERROR'}, "Please save the .blend file before exporting to a relative path (//)")
            return {"CANCELLED"}
        if not is_preset_setup_valid(scene, preset):
            self.report({'ERROR'}, "Improper setup: One or more override fields are missing or invalid.")
            return {"CANCELLED"}

        for c in preset.collections: sync_collection_objects(c)
        preset_root = os.path.normpath(bpy.path.abspath(scene.batch_stl_root_dir))
        with cached_menu_items():
            clashes = find_export_clashes(scene, preset, preset_root)
            targets = list(iter_export_objects(scene, preset))
        if clashes:
            self.report({'ERROR'}, f"Export aborted: {len(clashes)} files would be written more than once (e.g. {next(iter(clashes.values()))}). Check the tree view.")
            return {"CANCELLED"}

        context.window_manager.batch_stl_info_tab = 'LOG'
        job.console_logs.clear()

        for c in preset.collections:
            # e.g. the collection was renamed or deleted: say so instead of reporting a complete export
            if c.export and c.collection_name and not bpy.data.collections.get(c.collection_name):
                self._log(job, f"SKIPPED (collection not found): {c.collection_name}")

        # This process writes the objects without overrides that the view layer evaluates; the worker writes the rest,
        # in its copy, with their collections switched on. It tells them apart with the same test (is_direct) in the
        # job's view layer, which is this one: context.view_layer, as for the job file.
        live = live_collection_names(context.view_layer)
        objects_to_export_directly = [(c, obj_prop, bl_obj) for _c_idx, c, obj_prop, bl_obj, ovrs in targets if is_direct(bl_obj, ovrs, live)]
        needs_headless = len(objects_to_export_directly) < len(targets)

        # The worker goes first: it takes a second or more to boot, while the direct objects are written meanwhile.
        # Its snapshot is taken before the direct export touches the scene (it unhides eye-hidden objects for a moment).
        if needs_headless and not self._start_worker(context, scene, preset, job): return {'CANCELLED'}

        # Resolve every path now (the settings are the ones at the click); _export_direct finds the objects again by name.
        for c, obj_prop, bl_obj in objects_to_export_directly:
            full_dir_parts, filename = export_file_parts(preset, c, obj_prop, bl_obj)
            out_dir = os.path.normpath(os.path.join(preset_root, *full_dir_parts)) if full_dir_parts else preset_root
            label = f"{preset.name} | {c.collection_name} | {bl_obj.name} | Permutation 1/1 | Batch 1/1"
            self.direct_queue.append((c.collection_name, bl_obj.name, os.path.join(out_dir, filename), label))
        self.direct_total = len(self.direct_queue)

        if not self.direct_queue and not needs_headless:
            preset.last_export_time = time.perf_counter() - self.export_start_time
            self._log(job, f"=== BATCH EXPORT COMPLETE ({preset.last_export_time:.4f}s) ===")
            self.report({'INFO'}, f"Batch Export {preset.name} Complete in {preset.last_export_time:.2f}s.")
            redraw_sidebars(context)
            self.cleanup(context)
            return {'FINISHED'}

        job.is_exporting, job.cancel_export, job.export_progress = True, False, 0.0
        return {'RUNNING_MODAL'}

    def _start_worker(self, context, scene, preset, job):
        """Save the snapshot the worker opens, write its job file and start it. False (reported) when it did not start."""
        job.export_status = "Spawning Worker... (0.0s)"
        t_spawn_start = time.perf_counter()
        self.temp_dir = tempfile.mkdtemp(prefix=TEMP_PREFIX)
        self.temp_blend = os.path.join(self.temp_dir, "batch_stl_export_temp.blend")
        self.job_json = os.path.join(self.temp_dir, "job.json")

        bpy.ops.wm.save_as_mainfile(filepath=self.temp_blend, copy=True, compress=False)
        # context.view_layer, as for `live` in _start: the worker skips the objects written directly by the same test
        write_job_file(self.job_json, scene, context.view_layer, preset, bpy.path.abspath(scene.batch_stl_root_dir), skip_direct=True)

        # The standby worker (when the preference keeps one ready) opens the snapshot as soon as it gets the job, so
        # Blender's boot is not part of the export. Otherwise a worker starts with WORKER_SCRIPT, which loads this package
        # from its folder and runs the job. Either way the worker writes its output to a file that _poll reads.
        autoexec = context.preferences.filepaths.use_scripts_auto_execute
        standby = take_standby(autoexec)
        if standby is not None and standby.send(self.temp_blend, self.job_json):
            self.process, self.output, self.worker_dir = standby.process, standby.output, standby.folder
            self._log(job, f"=== INITIATING HEADLESS EXPORT '{preset.name}' [standby worker, {time.perf_counter() - t_spawn_start:.4f}s] ===")
        else:
            if standby is not None: standby.stop()
            self.output = WorkerOutput(os.path.join(self.temp_dir, "worker.log"))
            try:
                self.process = start_process(worker_args(autoexec, "-b", self.temp_blend, "-P", WORKER_SCRIPT, "--", "--batch-stl-headless", self.job_json), self.output.path)
            except Exception as e:
                self.report({'ERROR'}, f"Failed to spawn headless Blender: {e}")
                self.cleanup(context)
                return False
            self._log(job, f"=== INITIATING HEADLESS EXPORT '{preset.name}' [{time.perf_counter() - t_spawn_start:.4f}s Boot] ===")
        self.worker_done = False
        return True

    def _export_direct(self, context, job, budget):
        """Write the queued objects without overrides, for about `budget` seconds (None: all of them), but at least one.
        The first call also collects the instances of all of them in one pass over the depsgraph."""
        t_start = time.perf_counter()
        depsgraph = context.evaluated_depsgraph_get()
        if self.instance_arrays is None:
            self._log(job, f"=== STARTING NATIVE DIRECT EXPORT ({self.direct_total} Objects) ===")
            objects = (find_direct_object(entry[0], entry[1]) for entry in self.direct_queue)
            self.instance_arrays = collect_instance_arrays(depsgraph, [ob for ob in objects if ob])
        while self.direct_queue:
            collection_name, object_name, filepath, label = self.direct_queue.popleft()
            t_object = time.perf_counter()
            bl_obj = find_direct_object(collection_name, object_name)
            if bl_obj:
                result_text = export_object_stl(filepath, bl_obj, depsgraph, self.instance_arrays.get(bl_obj.name_full, ()))
            else:
                result_text = f"SKIPPED (object no longer in the collection): {filepath}"
            self.direct_done += 1
            self._log(job, f"{label}\n  └─ {result_text} | {time.perf_counter() - t_object:.2f} s")
            if budget is not None and time.perf_counter() - t_start >= budget: break
        if self.process is None: job.export_progress = self.direct_done / max(1, self.direct_total)

    def _preset(self):
        """The preset being exported, or None when an undo removed it (the export carries on regardless)."""
        return find_preset(self.scene_uid, self.preset_uid)

    def _job(self):
        return find_job(getattr(self, "scene_uid", 0), getattr(self, "preset_uid", ""))

    def _drain_output(self, job):
        """Process the lines the worker printed since the last poll. Returns True once it reported BATCH_STL_DONE."""
        for line in self.output.read_lines(stop="BATCH_STL_DONE"):
            if line.startswith("BATCH_STL_TOTAL:"):
                try: self.total_operations = int(line.split(":")[1])
                except Exception: pass
            elif line.startswith("BATCH_STL_PROGRESS:"):
                try:
                    self.current_op = int(line.split(":")[1])
                    job.export_progress = self.current_op / max(1, self.total_operations)
                except Exception: pass
            elif line.startswith("BATCH_STL_DONE"):
                return True
            elif line:
                self._log(job, line)
        return False

    def modal(self, context, event):
        result = self._poll(context, read_output=event.type == 'TIMER')
        return {'PASS_THROUGH'} if result == {'RUNNING_MODAL'} else result

    def _poll(self, context, read_output=True):
        """One step of the export: stop on a cancel, write the next queued objects without overrides, process the worker's
        output, and finish once the queue is empty and the worker is done or gone. Returns {'RUNNING_MODAL'} until then."""
        try:
            job = self._job()
            if job is None:  # a file load cleared the jobs: this export belonged to a file that is gone
                self.cleanup(context)
                return {'CANCELLED'}

            if job.cancel_export:
                self.cleanup(context)
                self.report({'WARNING'}, f"Export cancelled for {self.preset_name}.")
                return {'CANCELLED'}

            if read_output:
                if self.direct_queue: self._export_direct(context, job, self.direct_budget)
                elapsed = time.perf_counter() - self.export_start_time
                if not self.worker_done:
                    self.worker_done = self._drain_output(job)
                    if not self.worker_done and self.process.poll() is not None:
                        # The worker prints BATCH_STL_DONE right before exiting: read what it wrote after the first read
                        # (all of its output is in the file once it exited) before judging.
                        self.worker_done = self._drain_output(job)
                        if not self.worker_done:
                            exit_code = self.process.returncode
                            # The objects without overrides do not depend on the worker: they are written all the same.
                            if self.direct_queue: self._export_direct(context, job, None)
                            self.cleanup(context)
                            self._log(job, f"[!] CRASH DETECTED: Worker exited with code {exit_code} before finishing.")
                            self.report({'ERROR'}, f"Background worker crashed for preset {self.preset_name}.")
                            redraw_sidebars(context)
                            return {'CANCELLED'}

                # worker_done is kept: the worker's DONE line is read once, and it may finish before the queue does.
                if self.worker_done and not self.direct_queue:
                    self.cleanup(context)
                    preset = self._preset()
                    if preset: preset.last_export_time = elapsed
                    self._log(job, f"=== BATCH EXPORT COMPLETE ({elapsed:.4f}s) ===")
                    self.report({'INFO'}, f"Batch Export {self.preset_name} Complete in {elapsed:.2f}s.")
                    redraw_sidebars(context)
                    return {'FINISHED'}

                if self.direct_queue: job.export_status = f"Direct {self.direct_done}/{self.direct_total} | {elapsed:.1f}s"
                elif self.total_operations > 1 or self.current_op > 0: job.export_status = f"Obj {self.current_op}/{self.total_operations} | {elapsed:.1f}s"
                else: job.export_status = f"Spawning Worker... ({elapsed:.1f}s)"
                redraw_sidebars(context)
        except Exception:
            traceback.print_exc()
            self.cleanup(context)
            self.report({'ERROR'}, "Unexpected error during batch export.")
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        # Called by Blender when the modal is torn down from outside (e.g. loading another file).
        self.cleanup(context)

    def cleanup(self, context=None):
        if context and getattr(self, '_timer', None):
            try: context.window_manager.event_timer_remove(self._timer)
            except Exception: pass
            self._timer = None
        try:
            job = self._job()
            if job: job.is_exporting, job.cancel_export, job.export_progress, job.export_status = False, False, 0.0, ""
        except Exception: pass
        if getattr(self, 'process', None):
            try:
                if self.process.poll() is None:
                    self.process.kill()
                    self.process.wait(timeout=1.0)
            except Exception: pass
        # The export's own folder, and the standby worker's (its output file) when it ran the export
        for folder in (getattr(self, 'temp_dir', None), getattr(self, 'worker_dir', None)):
            if folder and os.path.exists(folder): shutil.rmtree(folder, ignore_errors=True)
        # The next export's worker: started once this one is done, so it does not compete with it
        ensure_standby()

def remove_stale_temp_dirs():
    """Remove the temp folders of exports that crashed. A recent one may belong to an export running in another Blender
    instance (its worker reads the folder after loading the file), so only old ones go."""
    try:
        tmp = tempfile.gettempdir()
        for f in os.listdir(tmp):
            path = os.path.join(tmp, f)
            if f.startswith(TEMP_PREFIX) and time.time() - os.path.getmtime(path) > STALE_TEMP_AGE:
                shutil.rmtree(path, ignore_errors=True)
    except Exception: pass

classes = (BATCH_STL_OT_cancel_export, EXPORT_OT_batch_stl_multi)
