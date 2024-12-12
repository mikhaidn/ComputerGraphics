from PIL import Image
import sys
import numpy as np
from typing import List
from .structures import Geometry, LightSource, Ray
from src.geometry.sphere import Sphere
from src.lightsource.sun import Sun

class Renderer:
    geometries: List[Geometry]

    def __init__(self):
        self.sRGB = True
        self.color = np.array([1, 1, 1])
        self.geometries: List[Geometry] = []
        self.lightSources: List[LightSource] = []
        self.debug = False

    def WithWidth(self, width):
        self.width = width
        return self

    def WithHeight(self, height):
        self.height = height
        return self

    def WithOutputFile(self, output_file):
        self.output_file = output_file
        return self

    def WithImage(self, image):
        self.image = image
        return self

    def AddSphere(self, r, position):
        sphere = Sphere(r, position, self.GetStates())
        self.geometries.append(sphere)
        return self

    def AddSun(self, position):
        sun = Sun(position, self.GetStates())
        self.lightSources.append(sun)
        return self

    def SetColor(self, rgb):
        self.color = np.array(rgb)
        return self

    def GetStates(self):
        states = {}
        states["color"] = self.color

        return states

    def RenderFrame(self):
        maxWidthOrHeight = max(self.width, self.height)
        for i in range(self.width):
            for j in range(self.height):
                eye, ray_direction = self.EmitRayFromIndex(maxWidthOrHeight, i, j)

                incomingLight = self.Trace(eye, ray_direction)

                self.image.putpixel((i, j), incomingLight)

    def EmitRayFromIndex(self, maxWidthOrHeight:float, i:float, j:float):
        eye = np.array([0, 0, 0])
        f = np.array([0, 0, -1])
        r = np.array([1, 0, 0])
        u = np.array([0, 1, 0])
        s = np.array([
            (2 * i - self.width) / maxWidthOrHeight,
            (self.height - 2 * j) / maxWidthOrHeight,
            0,
        ])

        s_x = s[0]  # 2*i - self.width/maxWidthOrHeight
        s_y = s[1]  # self.height - 2*j

        # Sum all terms and normaize
        ray_direction = f + s_x * r + s_y * u
        ray_direction /= np.linalg.norm(ray_direction)

        # self.debug = False
        # if i == 55 and j == 45:
        #     self.debug = True
        #     print(ray_direction)
        #     print([s_x, s_y, -1])
            
        return eye, ray_direction

    def Trace(self, position, direction):
        ray = Ray()
        ray.origin=np.array(position)
        ray.direction = np.array(direction)
        
        hitInfo = self.CalculateRayCollision(ray)

        if self.debug:
            print(ray)
            print(hitInfo)

        if hitInfo:
            return self.CalculateLight(hitInfo)

        # if hit - update image w/ material stuff
        # else return background color, using cyan for now
        # bg_color = tuple(np.asarray([0, 1, 1, 1] * 256).astype(int))
        # print(bg_color)
        return (0, 0, 0, 0)

    def CalculateLight(self, hitInfo):
        if hitInfo is None:
            return np.zeros(3)

        # Calculate illumination from all light sources and sum them
        total_illumination = np.zeros(3)
        for light in self.lightSources:
            illumination = light.calculate_illumination(hitInfo, self.debug)
            total_illumination += illumination

        return (
            int(total_illumination[0] * 255),
            int(total_illumination[1] * 255),
            int(total_illumination[2] * 255),
            255,
        )

    def CalculateRayCollision(self, ray:Ray):
        hits = [
            g.calculate_intersection(ray)
            for g in self.geometries
        ]
        valid_hits = [
            c for c in hits if c is not None and c.distance > 0
        ]
        if valid_hits:
            collision = min(valid_hits, key=lambda x: x.distance)

        else:
            return None

        shadow_origin = collision.point + collision.normal * 0.0000001

        # Check all lights for shadows
        collision.in_shadow = {}  # Dictionary to track shadow state per light
        for light in self.lightSources:
            to_light = light.get_direction_from_point(shadow_origin)
            shadow_ray = Ray()
            shadow_ray.origin = shadow_origin
            shadow_ray.direction = to_light
            
            # Check if anything blocks path to light
            shadow_hits = [g.calculate_intersection(shadow_ray) for g in self.geometries]
            collision.in_shadow[light] = any(hit is not None for hit in shadow_hits)


        return collision

    def save(self):
        print(self.image, self.height, self.width, self.output_file)

        if self.sRGB:
            srgb_image = convert_linear_to_srgb(self.image)
            self.image = srgb_image
        self.image.save(self.output_file)


def print_points(text, points):
    print("--- LOG: " + text + " begin")
    print("-------  ", [i[0:2] for i in points])
    print("--- LOG: " + text + " end")







def color(size, nums):
    """
    color size num0 num1 num2
     size is either  3, or 4
     RGBA
    """
    if size == 3:
        appending_tuple = [1]
    elif size == 4:
        appending_tuple = []
    else:
        return ValueError
    colors = [nums[i : i + size] + appending_tuple for i in range(0, len(nums), size)]
    return colors


def linear_to_srgb(linear):
    unclamped = np.where(
        linear < 0.0031308, linear * 12.92, 1.055 * (linear ** (1 / 2.4)) - 0.055
    )
    return np.clip(unclamped, 0.0, 1.0)


def convert_linear_to_srgb(img):
    # Convert image to numpy array
    img_array = np.array(img).astype(np.float32) / 255.0

    # Apply sRGB conversion
    srgb_array = linear_to_srgb(img_array)

    # Convert back to 8-bit integer
    srgb_array = (srgb_array * 255).astype(np.uint8)

    # Create new image from array
    srgb_image = Image.fromarray(srgb_array)

    # Save the result
    return srgb_image


