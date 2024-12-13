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

        self.shininess = np.array([0, 0, 0])
        self.transparency = np.array([0, 0, 0])
        self.transparency = np.array([0, 0, 0])

        self.roughness = float(0)
        self.ior = 1.458

        self.bounces = 4
        self.antiAliasing = 1

        self.focus = 0
        self.lens = 0
        self.globalIllumination = 0

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

    def SetShininess(self, rgb):
        if len(rgb) == 1:
            r = rgb[0]
            rgb = np.array([r, r, r])

        self.shininess = rgb
        return self

    def SetBounces(self, n):
        self.bounces = n
        return self

    def SetTransparency(self, rgb):
        if len(rgb) == 1:
            r = rgb[0]
            rgb = np.array([r, r, r])

        self.transparency = rgb
        return self

    def SetIor(self, nu):
        self.ior = nu
        return self

    def SetRoughness(self, rough):
        self.roughness = rough
        return self

    def SetAntiAliasing(self, n):
        self.antiAliasing = n
        return self

    def SetDepthOfField(self, dof):
        self.focus = dof[0]
        self.lens = dof[1]
        return self

    def SetGlobalIllumination(self, d):
        self.globalIllumination = d
        return self

    def GetStates(self):
        states = {}
        states["color"] = self.color
        states["texture"] = self.texture
        states["texcoord"] = self.texcoord

        states["shininess"] = self.shininess
        states["ior"] = self.ior
        states["transparency"] = self.transparency
        states["roughness"] = self.roughness

        return states

    def RenderFrame(self):
        maxWidthOrHeight = max(self.width, self.height)
        for i in range(self.width):
            for j in range(self.height):
                accumulated_rgb = np.zeros(3)
                accumulated_alpha = 0
                n = self.antiAliasing

                for _ in range(n):
                    if n > 1:
                        # Add jittered offsets
                        dx = (np.random.random() - 0.5) / maxWidthOrHeight
                        dy = (np.random.random() - 0.5) / maxWidthOrHeight
                    else:
                        dx, dy = (
                            0,
                            0,
                        )  # for backwards compatibility, don't do this the first time

                    eye, ray_direction = self.EmitRayFromIndex(
                        maxWidthOrHeight, i + dx, j + dy
                    )

                    color = self.Trace(eye, ray_direction)
                    color_array = np.array(color)

                    accumulated_rgb += color_array[:3]
                    accumulated_alpha += color_array[3]

                # I can't figure out the boundary thing :/
                final_rgb = accumulated_rgb / n
                final_alpha = accumulated_alpha / n
                final_color = (*[int(c) for c in final_rgb], int(final_alpha))

                self.image.putpixel((i, j), final_color)

    def EmitRayFromIndex(self, maxWidthOrHeight: float, i: float, j: float):

        s = np.array(
            [
                (2 * i - self.width) / maxWidthOrHeight,
                (self.height - 2 * j) / maxWidthOrHeight,
                1,
            ]
        )

        if self.panorama:
            longitude = (2 * i - self.width) * np.pi / self.width  # -pi to pi
            latitude = (
                (self.height - 2 * j) * np.pi / (2 * self.height)
            )  # -pi/2 to pi/2

            s = np.array(
                [
                    np.cos(latitude) * np.sin(longitude),
                    np.sin(latitude),
                    np.cos(latitude) * np.cos(longitude),
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

            # Modify only the forward component
            f = f * np.sqrt(1 - sum_of_squares)

        # Sum all terms and normaize
        ray_direction = f * s_z + s_x * r + s_y * u
        ray_direction /= np.linalg.norm(ray_direction)


        # Depth of field
        if self.lens > 0 and self.focus > 0:
            # Calculate focal point
            focal_point = self.eye + ray_direction * self.focus

            # Generate random point on lens
            theta = np.random.random() * 2 * np.pi
            radius = np.random.random() * self.lens

            # Calculate offset on lens plane
            lens_offset = radius * (
                np.cos(theta) * self.right + np.sin(theta) * self.up
            )

            # Update ray origin and direction
            new_origin = self.eye + lens_offset
            new_direction = focal_point - new_origin
            new_direction = new_direction / np.linalg.norm(new_direction)

            return new_origin, new_direction

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

        return (0, 0, 0, 0)

    def CalculateTransparency(self, hitInfo: HitInfo, current_depth: int) -> np.ndarray:
        """
        Calculate the transparency contribution with refraction through objects.
        """
        if current_depth > self.bounces or not np.any(hitInfo.transparency > 0):
            return np.zeros(3)

        N = hitInfo.normal
        I = hitInfo.incident_direction
        n1 = 1.0
        n2 = hitInfo.refraction_index

        a = -np.dot(N, I)
        b = 1 - (n1 / n2) ** 2 * (1 - a**2)

        # 'not' step 3
        if b < 0:
            return np.zeros(3)

        c = np.sqrt(b)
        refraction_direction = (n1 / n2) * I + ((n1 / n2) * a - c) * N
        refraction_direction = refraction_direction / np.linalg.norm(
            refraction_direction
        )

        # Trace through object to find exit point
        entry_ray = Ray()
        entry_ray.origin = hitInfo.point - N * self.epsilon
        entry_ray.direction = refraction_direction

        exit_hit = self.CalculateRayCollision(entry_ray)
        if exit_hit is None or exit_hit.material != hitInfo.material:
            return np.zeros(3)

        # Find outward refraction direction
        N_exit = exit_hit.normal
        I_exit = entry_ray.direction
        n1, n2 = n2, n1  # Swap indices for exit

        a_exit = -np.dot(N_exit, I_exit)
        b_exit = 1 - (n1 / n2) ** 2 * (1 - a_exit**2)

        if b_exit < 0:
            return np.zeros(3)

        c_exit = np.sqrt(b_exit)
        refraction_direction_exit = (n1 / n2) * I_exit + (
            (n1 / n2) * a_exit - c_exit
        ) * N_exit
        refraction_direction_exit = refraction_direction_exit / np.linalg.norm(
            refraction_direction_exit
        )

        # Continue ray trace from exit point
        exit_ray = Ray()
        exit_ray.origin = exit_hit.point - N_exit * self.epsilon
        exit_ray.direction = refraction_direction_exit

        final_hit = self.CalculateRayCollision(exit_ray)
        if final_hit is None:
            return np.zeros(3)

        refracted_color = self.CalculateLight(final_hit, current_depth + 1)
        return np.array(refracted_color[:3]) / 255.0 * hitInfo.transparency

    def CalculateReflection(self, hitInfo: HitInfo, current_depth: int) -> np.ndarray:
        """
        Calculate the reflection contribution with a maximum bounce depth.
        """
        # If bounce depth is reached, return black
        if current_depth > self.bounces:
            return np.zeros(3)

        # If surfance isn't shiny, return black
        specular_color = hitInfo.shininess
        if not np.any(specular_color > 0):
            return np.zeros(3)

        # Calculate reflection vector
        N = hitInfo.normal
        I = hitInfo.incident_direction
        reflection_vector = I - 2 * np.dot(I, N) * N

        reflection_direction = reflection_vector / np.linalg.norm(reflection_vector)

        # Trace reflection ray
        reflection_ray = Ray()
        reflection_ray.origin = hitInfo.point + hitInfo.normal * self.epsilon
        reflection_ray.direction = reflection_direction

        reflection_hit = self.CalculateRayCollision(reflection_ray)
        if reflection_hit is None:
            return np.zeros(3)

        # recurse with depth +1
        reflected_color = self.CalculateLight(reflection_hit, current_depth + 1)
        return np.array(reflected_color[:3]) / 255.0 * specular_color

    def CalculateLight(self, hitInfo: HitInfo, current_depth: int = 0):
        if hitInfo is None:
            return np.zeros(3)

        # Sum all light sources
        total_illumination = np.zeros(3)
        for light in self.lightSources:
            illumination = light.calculate_illumination(hitInfo, self.debug)
            total_illumination += illumination

        # Calculate reflection and refraction until depth
        if current_depth < self.bounces:
            reflection_contribution = self.CalculateReflection(hitInfo, current_depth)
            transparency_contribution = self.CalculateTransparency(
                hitInfo, current_depth
            )

            # Blend between direct illumination, reflection, and transparency
            shininess = hitInfo.shininess
            transparency = hitInfo.transparency
            opacity = 1 - transparency

            total_illumination = (
                total_illumination * opacity * (1 - shininess)  # Direct illumination
                + reflection_contribution * opacity  # Reflection
                + transparency_contribution  # Refraction
            )

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
