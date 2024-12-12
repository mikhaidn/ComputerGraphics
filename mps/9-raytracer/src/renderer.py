from PIL import Image
import sys
import numpy as np
from typing import List
from numpy.typing import NDArray
from src.lightsource.bulb import Bulb
from texure_handler import load_texture


from src.geometry.plane import Plane
from src.geometry.triangle import Triangle
from .structures import Geometry, HitInfo, LightSource, Ray, Vertex
from src.geometry.sphere import Sphere
from src.lightsource.sun import Sun


class Renderer:
    geometries: List[Geometry]

    def __init__(self):
        self.sRGB = True
        self.color = np.array([1, 1, 1])
        self.geometries: List[Geometry] = []
        self.lightSources: List[LightSource] = []
        self.vertecies: List[Vertex] = []
        self.epsilon = 0.00000001
        self.debug = False
        self.exposure = None
        self.eye = np.array([0, 0, 0])
        self.forward = np.array([0, 0, -1])
        self.right = np.array([1, 0, 0])
        self.up = np.array([0, 1, 0])

        self.fisheye = False
        self.panorama = False

        self.texcoord = (0, 0)
        self.texture = None

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

    def WithExposure(self, exposure):
        self.exposure = exposure
        return self

    def AddSphere(self, r, position):
        sphere = Sphere(r, position, self.GetStates())
        self.geometries.append(sphere)
        return self

    def AddPlane(self, abcd):
        plane = Plane(abcd, self.GetStates())
        self.geometries.append(plane)
        return self

    def AddSun(self, position):
        sun = Sun(position, self.GetStates())
        self.lightSources.append(sun)
        return self

    def AddBulb(self, position):
        bulb = Bulb(position, self.GetStates())
        self.lightSources.append(bulb)
        return self

    def AddVertex(self, xyz):
        vertex = Vertex()
        vertex.point = xyz
        vertex.texcoord = self.texcoord

        self.vertecies.append(vertex)
        return self

    def AddTriangle(self, indecies):

        i0, i1, i2 = [idx - 1 if idx > 0 else idx for idx in indecies]

        v0 = self.vertecies[i0]
        v1 = self.vertecies[i1]
        v2 = self.vertecies[i2]
        triangle = Triangle(v0, v1, v2, self.GetStates())
        self.geometries.append(triangle)
        return self

    def SetFisheye(self):
        self.fisheye = True
        return self

    def SetPanorama(self):
        self.panorama = True
        return self

    def SetColor(self, rgb):
        self.color = np.array(rgb)
        return self

    def SetTexcoord(self, uv):
        u, v = uv
        self.texcoord = (u, v)
        return self

    def SetTexture(self, filename):
        if filename == "none":
            self.texture = None
        else:
            self.texture = load_texture(filename)
        return self

    def SetUp(self, direction):
        self.up = np.array(direction)
        return self

    def SetEye(self, direction):
        self.eye = np.array(direction)
        return self

    def SetForward(self, direction):
        self.forward = np.array(direction)

        r = np.cross(self.forward, self.up)
        self.right = r / np.linalg.norm(r)

        u = np.cross(self.right, self.forward)
        self.up = u / np.linalg.norm(u)
        return self

    def GetStates(self):
        states = {}
        states["color"] = self.color
        states["texture"] = self.texture
        states["texcoord"] = self.texcoord

        return states

    def RenderFrame(self):
        maxWidthOrHeight = max(self.width, self.height)
        for i in range(self.width):
            for j in range(self.height):
                eye, ray_direction = self.EmitRayFromIndex(maxWidthOrHeight, i, j)

                incomingLight = self.Trace(eye, ray_direction)

                self.image.putpixel((i, j), incomingLight)

    def EmitRayFromIndex(self, maxWidthOrHeight: float, i: float, j: float):

        s = np.array(
            [
                (2 * i - self.width) / maxWidthOrHeight,
                (self.height - 2 * j) / maxWidthOrHeight,
                1,
            ]
        )

        if self.panorama:
            longitude = (2 * i - self.width) * np.pi / self.width  # -π to π
            latitude = (self.height - 2 * j) * np.pi / (2 * self.height)  # -π/2 to π/2

            s = np.array(
                [
                    np.cos(latitude) * np.sin(longitude),  # x
                    np.sin(latitude),  # y
                    np.cos(latitude) * np.cos(longitude),  # z
                ]
            )

        s_x = s[0]  # 2*i - self.width/maxWidthOrHeight
        s_y = s[1]  # self.height - 2*j
        s_z = s[2]

        eye = self.eye
        f = self.forward
        r = self.right
        u = self.up

        if self.fisheye:
            sum_of_squares = s_x * s_x + s_y * s_y
            if sum_of_squares > 1:
                return None, None

            # Modify the forward component for this ray only
            f = f * np.sqrt(1 - sum_of_squares)

        # Sum all terms and normaize
        ray_direction = f * s_z + s_x * r + s_y * u
        ray_direction /= np.linalg.norm(ray_direction)

        # self.debug = False
        # if i == 55 and j == 45:
        #     self.debug = True

        return eye, ray_direction

    def Trace(self, position, direction):
        if position is None:
            return (0, 0, 0, 0)

        ray = Ray()
        ray.origin = np.array(position)
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

    def CalculateLight(self, hitInfo: HitInfo):
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

    def CalculateRayCollision(self, ray: Ray):
        hits = [g.calculate_intersection(ray) for g in self.geometries]
        valid_hits = [c for c in hits if c is not None and c.distance > 0]
        if valid_hits:
            collision = min(valid_hits, key=lambda x: x.distance)

        else:
            return None

        shadow_origin = collision.point + collision.normal * self.epsilon
        # Check all lights for shadows
        collision.in_shadow = {}  # Dictionary to track shadow state per light
        for light in self.lightSources:
            to_light = light.get_direction_from_point(shadow_origin)
            shadow_ray = Ray()
            shadow_ray.origin = shadow_origin
            shadow_ray.direction = to_light

            # Check if anything blocks path to light
            shadow_hits = [
                g.calculate_intersection(shadow_ray) for g in self.geometries
            ]
            collision.in_shadow[light] = min(
                (hit.distance for hit in shadow_hits if hit is not None), default=False
            )

        return collision

    def PostProcess(self):
        img_array = np.array(self.image).astype(np.float32) / 255.0

        if self.exposure is not None:
            img_array = apply_exposure(img_array, self.exposure)

        if self.sRGB:
            img_array = linear_to_srgb(img_array)

        # Convert back to 8-bit integer
        img_array = (img_array * 255).astype(np.uint8)
        self.image = Image.fromarray(img_array)

    def save(self):
        print(self.image, self.height, self.width, self.output_file)

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


def handle_alpha(rgb_operation):
    """Decorator that applies an operation to RGB channels only, preserving alpha if it exists"""

    def wrapper(image, *args, **kwargs):
        if image.shape[-1] == 4:
            rgb = image[..., :3]
            alpha = image[..., 3:]
            processed_rgb = rgb_operation(rgb, *args, **kwargs)
            return np.concatenate([processed_rgb, alpha], axis=-1)
        return rgb_operation(image, *args, **kwargs)

    return wrapper


@handle_alpha
def apply_exposure(linear, exposure):
    print("Max linear value before exposure:", np.max(linear))  # Debug

    return 1 - np.exp(-exposure * linear)


@handle_alpha
def linear_to_srgb(linear):
    unclamped = np.where(
        linear < 0.0031308, linear * 12.92, 1.055 * (linear ** (1 / 2.4)) - 0.055
    )
    return np.clip(unclamped, 0.0, 1.0)
