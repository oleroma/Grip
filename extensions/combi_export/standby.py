"""The standby worker: with the "Keep Worker Ready" preference on, a background Blender is started ahead of time. It
boots, imports this package and waits; an export hands it the snapshot and the job file instead of starting a worker,
which saves Blender's boot (2-3 s) at the click (ARCHITECTURE.md, Standby Worker)."""
import atexit
import json
import os
import queue
import subprocess
import sys
import threading

import bpy

from .headless import WORKER_SCRIPT

# The worker prints this once it is ready for a job; what it printed before (Blender's banner) is not part of any export
READY_LINE = "BATCH_STL_READY"

_standby = None  # the StandbyWorker waiting for a job, if any

def worker_args(autoexec, *args):
    """Command line of a worker. --factory-startup disables Python auto-run, so mirror the user's setting to keep
    scripted drivers working (`autoexec`). --python-exit-code: a Python error in the worker exits with code 1 instead
    of 0. `args` go after the blend file and script options."""
    return [bpy.app.binary_path, "--factory-startup", "--python-exit-code", "1", *(["--enable-autoexec"] if autoexec else []), *args]

def start_process(args):
    """Start a worker with its input and output (stdout and stderr) piped."""
    # blender.exe is a console program: without this flag Windows opens a console window for the worker.
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                               encoding="utf-8", errors="replace", env=dict(os.environ, PYTHONUNBUFFERED="1"), creationflags=flags)
    return process

class StandbyWorker:
    """A worker started without a job. Its lines go to `q` once it printed READY_LINE (`ready`); `t` reads them."""
    def __init__(self, autoexec):
        self.autoexec = autoexec
        self.ready = threading.Event()
        self.q = queue.Queue()
        self.process = start_process(worker_args(autoexec, "-b", "-P", WORKER_SCRIPT, "--", "--batch-stl-headless", "--standby"))
        self.t = threading.Thread(target=self._read, daemon=True)
        self.t.start()

    def _read(self):
        for line in iter(self.process.stdout.readline, ''):
            if self.ready.is_set(): self.q.put(line)
            elif line.startswith(READY_LINE): self.ready.set()
        self.process.stdout.close()

    def alive(self): return self.process.poll() is None

    def send(self, blend_path, job_path):
        """Hand the worker its job: it opens `blend_path` and runs `job_path`. False when it is gone."""
        try:
            self.process.stdin.write(json.dumps([blend_path, job_path]) + "\n")
            self.process.stdin.flush()
            return True
        except OSError:
            return False

    def stop(self):
        try:
            if self.alive():
                self.process.kill()
                self.process.wait(timeout=1.0)
        except Exception: pass

def get_preferences():
    """The add-on's preferences; None when the package is not enabled as an add-on (e.g. loaded by the tests)."""
    addon = bpy.context.preferences.addons.get(__package__)
    return addon.preferences if addon else None

def standby_enabled():
    """The "Keep Worker Ready" preference, off in background Blender (scripts, the tests, workers)."""
    prefs = get_preferences()
    return bool(prefs and prefs.keep_worker_ready) and not bpy.app.background

def ensure_standby():
    """Start the standby worker when the preference is on and none is running (or the last one died)."""
    global _standby
    if not standby_enabled(): return
    if _standby is not None and _standby.alive(): return
    try: _standby = StandbyWorker(bpy.context.preferences.filepaths.use_scripts_auto_execute)
    except Exception as e:
        _standby = None
        print(f"Combi Export: could not start the standby worker: {e}")

def take_standby(autoexec):
    """The standby worker for an export, once it is ready and was started with the `autoexec` setting the export needs;
    None otherwise (the export starts its own worker). The caller owns what it returns; a standby that does not fit is
    stopped (a new one starts when the export ends)."""
    global _standby
    worker, _standby = _standby, None
    if worker is None: return None
    if worker.alive() and worker.autoexec == autoexec:
        if worker.ready.is_set(): return worker
        _standby = worker  # still booting: keep it for the next export
        return None
    worker.stop()
    return None

def stop_standby():
    global _standby
    if _standby is not None: _standby.stop()
    _standby = None

def on_keep_worker_ready_update(self, context):
    if self.keep_worker_ready: ensure_standby()
    else: stop_standby()

def _start_after_register():
    ensure_standby()
    return None

def schedule_standby():
    """Start the standby worker shortly after the add-on is enabled (not during Blender's start itself)."""
    if not bpy.app.timers.is_registered(_start_after_register):
        bpy.app.timers.register(_start_after_register, first_interval=2.0)

def unschedule_standby():
    if bpy.app.timers.is_registered(_start_after_register): bpy.app.timers.unregister(_start_after_register)

# The worker also exits on its own once Blender is gone (its stdin closes); this stops one that is still booting.
atexit.register(stop_standby)

class BatchSTLPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__
    keep_worker_ready: bpy.props.BoolProperty(
        name="Keep Worker Ready", default=False, update=on_keep_worker_ready_update,
        description=("Keep a background Blender started and waiting for the next export, so exports with overrides "
                     "start at once instead of after Blender's boot (2-3 s). It holds about 250 MB of memory while idle"))

    def draw(self, context):
        self.layout.prop(self, "keep_worker_ready")

classes = (BatchSTLPreferences,)
