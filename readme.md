<h1 align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./media/logo_light.svg">
    <source media="(prefers-color-scheme: light)" srcset="./media/logo_dark.svg">
    <!-- The fallback image for older browsers -->
    <img alt="Project Title" src="./media/logo_light.svg" width="200">
  </picture>
  <br>
</h1>

# GRIP

*(Work in progress... release coming soon)*

---

## **FEATURES AND PROGRESS**

### CASE SHAPES

The project will include the following **CASE SHAPES**: 
1. 2 smooth, classic shapes in Xbox and DualSense styles.
2. Custom ergonomic "pistol-like" shape with stock-style bumpers (or just stock—no cursor jumping on this version).
3. SNES-style shape for portability (bonus shape).
4. Experimental custom ergonomic "pistol-like" shape with compliant bumpers (will be released as experimental; currently exhibits cursor jumping).

### FULL-SIZE RIGHT STICK

By default, the custom ergonomic shape (and possibly the classic shape) will use horizontally printed buttons with caps, as they provide a better feel, tighter tolerances, and less squeak. A great advantage of horizontal buttons is that when used with caps, their shafts are much smaller. Combined with a thinner scroll wheel and a new custom wheel support, this allows for a **FULL-SIZE RIGHT STICK** with a shield. This means you can have identical left and right sticks.

### BLENDER PROJECT WITH NODES

The final **BLENDER** project, built with **GEOMETRY NODES**, will be released and **WILL FEATURE** procedural generation for:

1. **Buttons:** Vertically or horizontally printed (very smooth, much quieter, less squeaky, and with tighter tolerances) with snap-on **caps**. Features customizable tolerances, **cap shapes** (want star- or heart-shaped buttons? You can have any shape!), and custom button logos (easily add any letter or symbol to the top of your buttons).
2. **Sticks:** Customizable range (specify the maximum tilt angle), size, height, stick-top shape, and cutout hole (circle, square, hexagon, or octagon). Also features customizable top texture and profile (convex, concave, or flat; square or circle).
3. **Bumpers (L1/R1):** Tunable size, shape, tolerances, and dimensions (width, height, and depth of the button).
4. **Arch-Shaped Triggers (L2/R2, L4/R4):** Tunable size, shape, positions, press angles, and tolerances (**no screws required**). You can move them inward, outward, up, or down to match your exact fingertip resting positions.
5. **Battery Cover:** Customizable battery compartment size, thickness, etc.
6. **Scroll Wheel:** Customizable diameter and width.

> **Tip:** You can easily swap the case for your own custom shape by placing your mesh into the corresponding "basemesh" collection—just drop it into the collection, and it will automatically be sliced and cut.

### **PROCEDURAL SHELL OPTIONS**

All shapes will come with an optional "hollow" version (generated using Signed Distance Fields, or SDFs) that can be either a shell-like structure or a lattice-like structure with holes.

* **Hollow Version:** A 3-part assembly consisting of a top case, a bottom case, and a middle plate that holds the PCB. 
* **Solid Version:** Includes optional grip texturing featuring **periodic surface patterns** such as: Gyroid, Cubic, Primitive, Diamond, Voronoi, and Fischer-Koch S/CY.

### **NO-SCREWS OPTION**

The solid version is designed to be held together with screws. The hollow version does not require screws for assembly, though you can still add them if preferred.

### **RELEASE PLAN**

All versions will be released as separate `.3mf` files for OrcaSlicer, along with `.stl` files. Releases will roll out as soon as testing is complete, starting with the solid versions and progressing to the more complex models.

### **PRINTING**

The project is optimized for FDM 3D printers, but it is also suitable for SLS and SLA printing—especially the hollow version.

---

## **CURRENT STATE**

Everything is functional, assembles properly, and fits well.

* **Solid Version:** 90% complete. Currently fine-tuning case shapes and button positions.
* **Hollow Version:** 80% complete. Currently fine-tuning assembly tolerances.
* **Blender Project:** 80% complete. The underlying logic is robust and functional. The UI is still a bit messy and may feel overwhelming due to the large number of parameters. Need to polish the layout and create simplified controls for frequently used parameters (e.g., tolerances and trigger positions).

---

## **TO DO**
 
1. Create documentation and a video guide on printing, cleaning, and assembly.
2. Create `.3mf` files for each version.
3. Polish the `.blend` project UI.

> **NOTE:** The initial release will be a **beta**. If you are willing to be a tester, please let us know!

**Credits:** Oleroma, Milwud

---

## **DEPENDENCIES**
* Git LFS
* Blender >= 4.x

## **LFS AND FILE DOWNLOAD**

If you want to download the Blender and STL files, **DO NOT USE the "Download ZIP" button** on GitHub. It is not compatible with LFS (Large File Storage). Instead, please clone the repository directly.

To use Git with this project, you must first install [Git Large File Storage](https://git-lfs.github.com).
