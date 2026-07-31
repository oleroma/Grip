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
(Work in progress... release is soon)


# **FEATURES AND PROGRESS**
## CASE SHAPES

Project will include such **CASE SHAPES**: 
1. 2 smooth classic case shapes, Xbox and Dualsense  style.
2. Custom ergo "pistol like" shape with stock style bumpers (or just with stock, no cursor jumping on this version)
3. SNES style shape, for portability (bonus shape)
4. experimental custom ergo "pistol like" with compliant bumpers (will be released as experimental, exhibits cursor jumping)

## FULL SIZE RIGHT STICK

By default custom ergo (and maybe classic shape) will go with horizontally printed buttons with caps, since they provide better feel, tighter tolerances and less squeak.Cool thing about horizontal buttons is that if used with caps, their shafts are much smaller, and when combined with thinner scroll wheel and new custom wheel support, it allows to have **FULL SIZE RIGHT STICK** with shield. That means you can have identical left and right sticks.

## BLENDER PROJECT WITH NODES

In the end **BLENDER** project that realized with **GEOMETRY NODES** will be released and **WILL FEATURE**:

1. **Procedural buttons** vertically printed or horizontally printed (very smooth, much quieter, less sqeaky, tighter tolerances) with snap-on **caps**. Customizable tolerances, **cap shapes** (you want star or heart shaped buttons? why not, you can have it, any shape), custom button logos (you can put letter or any symbol on top of your button easily).

2. Procedural sticks with customizable range(you can specify max angle it would tilt), size, height, shape of the  stick top and cutout hole (circle, square, hexagon,or octagon), customizable top texture and shape(convex, concave or flat, square or circle)

3. Customizable bumpers, size, shape, tolerances, etc (width, height and depth of the button)

4. Cutomizable arch shaped R2R4 triggers (that **do not require screws**), tunable size, shape, postions, press angles, tolerances (you can move them more inward or outward, up and down exactly where your fingertips arrive and where you want them)

5. Procedural battery cover, customizable battery size, thickness etc.

6. Case shape can be changed easily for your own shape just putting it into corresponding "basemesh" collection (you just drop it into collection, and it gets sliced and cut)

7. Customizable scrollwheel diameter and width.

## **PROCEDURAL SHELL OPTIONS**


All shapes will come with optional "hollow" version (made using signed distance fields)that will be either shell like structure or lattice like structure with holes.

Hollow version will be a 3 part assembly from top/bottom case and middle plate that holds pcb. 
Solid version would also have optional grip texturing that will include such **periodic surface patterns** as: gyroid, cubic, primitive, diamond, voronoi, FischerKoch CY/S.

## **NO SCREWS OPTION**

Solid version would be held with screws but hollow version, does not require them, though you could still have them if you want. 

## **Release**

All versions would be released as separate 3mf for orca slicer with STLs as soon as they tested out sufficiently starting from solid versions and then following the complexity.

## **PRINTING**
Project is tuned for FDM 3D printers, but potentially is good for SLA, SLA, especially hollow version.

## **CURRENT STATE**

Everything is working, assembles and fits.

Solid version 90% complete. Tuning case shapes and button positions.

Hollow version 80% complete. Tuning assembly tolerances.

Blender project 80% percent ready. Logic is robust, everything works. A bit messy UI and might be overwhelming because it has a lot of parameters. Neet to pretty everything, and make simplified controls that will include most used parameters like tolerances for example or trigger positions. 

## **TO DO**
 
1. Documentation, video guide on printing, cleaning and assembly

2. Create .3mf for each version

3. Pretty .blend project

## **NOTE**: first release would be "beta", and anyone who is willing to be a tester, let me know.

Oleroma 
Milwud 

## Dependencies
- Git LFS.
- Blender >= 4.x.

## LFS and file download
If you only want to download the Blender and STL files `DO NOT USE download ZIP` GitHub button, since it is not compatible with LFS (Large File Storage), but instead clone the repo.

To use Git with this project it is required to install Git [Large File Storage](https://git-lfs.github.com).
