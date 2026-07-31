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

Project will include such **CASE SHAPES**: 
1. 2 smooth classic case shapes, Xbox and Dualsense  style.
2. Custom ergo "pistol like" shape with stock style triggers (or just with stock). No jumping on this version.
3. SNES style shape, for portability (bonus shape)
4. experimental custom ergo "pistol like" with compliant bumpers (will be released as experimental, exhibits cursor jumping)
By default custom ergo (and maybe classic shape) will go with horizontally printed buttons with caps, since they provide better feel, tighter tolerances and less squeak.

In the end **BLENDER** project will be released that **WILL FEATURE**:
1. Procedural buttons vertically printed or horizontally printed (very smooth, much quieter, less sqeaky, tighter tolerances) with snap-on caps. Customizable tolerances, cap shapes, base shapes, custom button logos.
2. Procedural sticks with customizable range, size, height, shape of the  stick top and cutout hole, customizable top texture.
3. Customizable bumpers, size, shape, tolerances, etc.
4. Cutomizable arch triggers R2R4, size, shape, postions, press angles, tolerances.
5. Procedural battery cover, customizable battery size, thickness etc.
6. Case shape can be changed easily for your own shape just putting it into corresponding "basemesh" collection.
7. Customizable scrollwheel diameter and width.

All shapes will come with optional "hollow" version that will be either shell like structure or lattice like structure with holes.
Hollow version will be a 3 part assembly from top/bottom  case and middle plate that holds pcb. 
Solid version would also have optional peroidic surface style grip texturing that will include: gyroid, cubic, primitive, diamond, voronoi, FischerKoch CY/S.


All versions would be released as separate 3mf for orca slicer as soon as they tested out sufficiently starting from solid versions and then following the complexity.
Project is tuned for FDM 3D printers, but potentially is good for SLA, SLA, especially hollow version.

Cool thing about sticks, they can be full size and with shields, same for left and right stick on this mod thanks to capped buttons and thinner wheel that will feature custom wheel support. Smaller button shafts and thinner wheel gives just enough space to feature full size Right stick with shield.

**CURRENT STATE**: 
Everything is working, assembles and fits.

Solid version 90% complete. Tuning case shapes and button positions.

Hollow version 80% complete. Tuning assembly tolerances.

Blender project 80% percent ready. Logic is robust, everything works. A bit messy UI and might be overwhelming because it has a lot of parameters. Neet to pretty everything, and make simplified controls that will include most used parameters like tolerances for example or trigger positions. 

**TO DO**: 
1. Documentation, video guide on printing, cleaning and assembly.
2. Create .3mf for each version
3. Pretty .blend project

**NOTE**: first release would be "beta", and anyone who is willing to be a tester, let me know.

Oleroma 
Milwud 

## Dependencies
- Git LFS.
- Blender >= 4.x.

## LFS and file download
If you only want to download the Blender and STL files `DO NOT USE download ZIP` GitHub button, since it is not compatible with LFS (Large File Storage), but instead clone the repo.

To use Git with this project it is required to install Git [Large File Storage](https://git-lfs.github.com).
