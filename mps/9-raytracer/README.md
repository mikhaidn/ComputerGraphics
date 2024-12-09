https://cs418.cs.illinois.edu/website/mps/raytracer.html

# Raytracer

This programming assignment creates 3D imagery using ray tracing. In most other respects, its logistics are similar to [the rasterizer assignment](https://cs418.cs.illinois.edu/website/mps/rasterizer.html): you code in any language you want and your program reads a text file and produces an image file.

## 1. Core

Implement a raytracer with spheres, diffuse lighting, and shadows. In particular, this means

1. Write a program that reads a `.txt` file and produces a `.png` file. It will be invoked as e.g. `./yourprogram exampleInput.txt`, via a [makefile](#what-you-submit).

2. Handle the input file keywords [`png`](#png-width-height-filename), [`color`](#color-r-g-b), [`sphere`](#sphere-x-y-z-r), and one [`sun`](#sun-x-y-z), with proper handling of sRGB gamma.

3. Implement the ray-sphere intersection algorithm. These algorithms are defined down to the pixel in almost all contexts, and should match [the provided input files and their outputs](#test-files) very closely. Almost all successful submissions follow [our ray-sphere intersection pseduocode](https://cs418.cs.illinois.edu/website/text/rays.html#ray-sphere-intersection) closely.

4. Implement shadows with [shadow rays](https://cs418.cs.illinois.edu/website/text/rays.html#secondary-rays), including preventing shadow acne.

## 2. Electives

You may stop after implementing the core parts. Elective parts may be implemented in any set of MPs, and getting 0 electives here is fine if you do extra electives elsewhere.

| Pt | Task | Prereqs | Keywords | Test cases |
|----|------|----------|----------|------------|
| 0.5 | exposure | | [`expose`](#expose-v) | ray-expose1.txt and ray-expose2.txt |
| 0.5 | suns | | more than one [`sun`](#sun-x-y-z) | ray-suns.txt and ray-shadow-suns.txt |
| 1 | camera | | [`eye`](#eye-ex-ey-ez), [`forward`](#forward-fx-fy-fz), [`up`](#up-ux-uy-uz) | ray-view.txt |
| 1 | lenses | | [`fisheye`](#fisheye), [`panorama`](#panorama) | ray-fisheye.txt and ray-panorama.txt |
| 1 | plane | | [`plane`](#plane) | ray-plane.txt and ray-shadow-plane.txt |
| 2 | triangle | plane | [`xyz`](#xyz),`tri` | ray-tri.txt and ray-shadow-triangle.txt |
| 1 | map | | [`texture`](#texture) | ray-tex.txt |
| 2 | barycentric | map, triangle | [`texcoord`](#texcoord-u-v) | ray-trit.txt |
| 2 | bulb | suns | [`bulb`](#bulb) | ray-bulb.txt and ray-shadow-bulb.txt and ray-neglight.txt |
| 2 | reflect | | [`shininess`](#shininess), [`bounces`](#bounces-d) | ray-shine1.txt and ray-shine3.txt and ray-bounces.txt |
| 2 | refract | reflect | [`transparency`](#transparency), [`ior`](#ior) | ray-trans1.txt and ray-trans3.txt and ray-ior.txt |
| 2 | rough | reflect | [`roughness`](#roughness) | ray-rough.txt |
| 2 | antialias | | [`aa`](#aa) | ray-aa.txt |
| 1 | focus | antialias | [`dof`](#dof-focus-lens) | ray-dof.txt |
| 3 | global | antialias, triangle | [`gi`](#gi) | ray-gi.txt |
| 3 | BVH | suns | | render ray-many.txt in under 1 second |

## 3. What you submit

For this MP you submit one program, in any language of your choosing, that implements all of the core and any elective functionality you choose. The program will be executed as follows:

```bash
make build
make run file=rast-grey.txt
make run file=rast-smallgap.txt
# ...
make run file=rast-points2.txt
```

See the associated warm-up for more on how to set up a Makefile and generate PNG images.

It is tedious to grade output files for inputs you haven't implemented. Because of that you'll be asked to submit a file named `implemented.txt` which lists the optional parts you implemented; in particular, it should be a subset of the following:

```
exposure  
suns      
camera          
lenses          
plane      
triangle   
barycentric
map        
bulb       
reflect         
refract         
rough           
antialias   
focus           
global          
BVH             
```

Submitting a file that says you implemented something you didn't may result in a small professionalism penalty for wasting grader time.

## 4. Test Files

All test input files, reference output files, and supporting files can be downloaded [as a zip](https://cs418.cs.illinois.edu/website/mps/files/raytracer-files.zip)

### 4.1 Core

[Core test files and examples]

### 4.2 Elective 

[Elective test files and examples]

## 5. Specification and implementation guide

### 5.1 Ray Emission

Rays will be generated from a point to pass through a grid in the scene. This corresponds to "flat projection," the same kind that frustum matrices achieve. Given an image w pixels wide and h pixels high, pixel (x, y)'s ray will be based the following scalars:

```
sx = (2x - w) / max(w, h)
sy = (h - 2y) / max(w, h)
```

These formulas ensure that sx and sy correspond to where on the screen the pixel is: sx is negative on the left, positive on the right; sy is negative on the bottom, positive on the top. To turn these into rays we need some additional vectors:

- **e**: the eye location; initially (0, 0, 0). A point, and thus not normalized.
- **f**: the forward direction; initially (0, 0, -1). A vector, but not normalized: longer forward vectors make for a narrow field of view.
- **r**: the right direction; initially (1, 0, 0). A normalized vector, always perpendicular to f.
- **u**: the up direction; initially (0, 1, 0). A normalized vector, always perpendicular to both r and f.

The ray for a given (sx, sy) has origin **e** and direction **f** + sx**r** + sy**u**.

### 5.2 Ray Collision

Each ray might collide with many objects. Each collision can be characterized as o + td for the ray's origin point o and direction vector d and a numeric distance t. Use the closest collision in front of the eye (that is, the collision with the smallest positive t).

Raytracing requires every ray be checked against the full scene of objects. As such your code will proceed in two stages:
1. Stage 1 reads the input file and sets up a data structure storing all objects
2. Stage 2 loops over all rays and intersects each with objects in the scene

Unlike the rasterizer, there is no explicit "draw" instruction: all scene geometry in the input file is drawn after you read the whole file.

Many of the elective parts of this assignment have rays spawn new rays upon collision. As such, most successful implementations have a function that, given a ray, returns which object it hit (if any) and where that hit occurred (the t value may be enough, but barycentric coordinates may also be useful); that ray-collision function is called from a separate function that handles lighting, shadows, and so on.

### 5.3 Illumination

Basic illumination uses Lambert's law: Sum (object color) times (light color) times (normal dot direction to light) over all lights to find the color of the pixel.

Make all objects two-sided. That is, if the normal points away from the ray (i.e. if d·n > 0), invert the normal before doing lighting.

Illumination will be in linear space, not sRGB, and in 0–1 space, not 0–255. If a color would be brighter than 1 or dimmer than 0, clamp it to the 0–1 range. You'll need to convert RGB (but not alpha) to sRGB yourself prior to saving the image.

### 5.4 State machine

To help the files not get messy when many different properties are specified, many options operate on a notional state machine.

For example, when you open the file the current color is white (1,1,1). Any `sphere` or `triangle` you see will be given the current color as its color. When you see a `color` command you'll change the current color. Thus in this file:

```
png 20 30 demo.png
sphere 0 0 0 0.1
color 1 0 0
sphere 0.5 0 0 0.2
sphere 0.3 0 0 0.3
color 0 1 0
```

The first sphere is white, the second and third spheres are red and the last `color` doesn't do anything.

## 6. Input keywords

The file may have three types of keywords:

1. The required `png` keyword will always be first
2. Mode-setting keywords are optional, but if present will precede any data or drawing keywords
3. State-setting keywords provide information for later geometry
4. Geometry keywords add objects to the scene, using both their parameters and the current state

No drawing happens until after the entire file is read.

### 6.1 PNG

#### `png` *width* *height* *filename*
- Always present in the input before any other keywords
- *width* and *height* are positive integers
- *filename* always ends `.png`
- Exactly the same as in the Rasterizer MP

### 6.2 Mode setting

#### `bounces` *d*
- Limits the depth of the secondary ray generation to *d*
- Primary rays have depth 0; secondary rays generated from a ray of depth x have depth x+1
- If the depth of a ray would be larger than *d*, don't generate that ray
- Defaults to 4 if not provided

#### `forward` *fx* *fy* *fz*
- Sets the forward vector for primary ray generation
- Do not normalize; if this vector is longer it will automatically result in a zoomed-in display
- Fix the right and up vectors to be perpendicular to forward

#### `up` *ux* *uy* *uz*
- Sets the target up vector, subject to being perpendicular to the forward vector
- See `forward` for how the real up vector is computed

#### `eye` *ex* *ey* *ez*
- Sets the ray origin for primary rays

#### `expose` *v*
- Sets the exposure function to use in converting light to screen color
- Apply exposure after all other computation and combination of colors, but before sRGB
- If present, use the function ℓexposed = 1 - e^(-vℓlinear)
- If absent, use the function ℓexposed = ℓlinear

#### `dof` *focus* *lens*
- Apply depth-of-field using a lens of radius *lens* and a focal depth of *focus*
- This is done by randomly perturbing each primary ray's origin and direction
- New origin should be a random location on a disk with radius *lens* and center `eye` which is perpendicular to the forward vector
- New direction should be picked such that oold + tdold = onew + tdnew where t is the focal depth

[Additional mode settings continue...]

### 6.3 State setting

#### `color` *r* *g* *b*
- Sets the current RGB color
- Given in RGB color space where 0 is black, 1 is white
- Do not clamp these values; negative and more-than-1 values are permitted
- Use the unclamped floating-point color values until the very end; the order is:
  1. All computation, including any antialiasing
  2. Exposure, if that mode is enabled
  3. Linear to sRGB, clamping to the 0–1 range
  4. sRGB to bytes
- Defaults to (1,1,1) if not provided

#### `texcoord` *u* *v*
- Sets a texture coordinate for subsequent `xyz` keywords
- Defaults to (0,0) if not provided

[Additional state settings continue...]

### 6.4 Geometry

#### `sphere` *x* *y* *z* *r*
- Add a sphere with center (x,y,z) and radius *r* to the list of objects to be rendered
- Capture any current state as part of the sphere's material

#### `sun` *x* *y* *z*
- Add an infinitely-far-away light source coming from direction (x,y,z)
- Capture the current color as the light's color

[Additional geometry settings continue...]