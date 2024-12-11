from PIL import Image
import sys
import numpy as np
from typing import Any, Protocol, List


class HitInfo(Protocol):
    didHit: bool
    hitDistance: float
    hitNormal: List[float]
    hitPoint: List[float]


class Geometry(Protocol):
    def calculate_intersection(self, origin: List, direction: List) -> HitInfo: ...


class Sphere(Geometry):
    def __init__(self, r, pos, state):
        self.r = r
        self.position = np.array(pos)
        self.state = state

    def calculate_intersection(self, origin, direction):
        # For clarity, let's map variables to the algorithm notation
        r_o = origin  # ray origin
        r_d = direction  # ray direction
        c = self.position  # sphere center
        r = self.r  # sphere radius

        # 1. Check if origin is inside sphere
        c_minus_ro = c - r_o
        inside = np.dot(c_minus_ro, c_minus_ro) < r * r

        # 2. Calculate t_c = (c - r_o)·r_d / ∥r_d∥
        t_c = np.dot(c_minus_ro, r_d) / np.dot(r_d, r_d)

        # 3. Early exit check
        if not inside and t_c < 0:
            return None

        # 4. Calculate d² = ∥r_o + t_c·r_d - c∥²
        closest_point = r_o + t_c * r_d - c
        d_squared = np.dot(closest_point, closest_point)

        # 5. Early exit check
        if not inside and r * r < d_squared:
            return None

        # 6. Calculate t_offset = √(r² - d²) / ∥r_d∥
        t_offset = np.sqrt(r * r - d_squared) / np.sqrt(np.dot(r_d, r_d))

        # 7. Calculate intersection point and distance
        if inside:
            t = t_c + t_offset
        else:
            t = t_c - t_offset

        intersection = r_o + t * r_d
        normal = (intersection - self.position) / np.linalg.norm(
            intersection - self.position
        )

        # Return dictionary with intersection information
        return {
            "distance": t,
            "intersection": intersection,
            "normal": normal,
            "sphere": self,
        }


class LightSource(Protocol):
    def calculate_illumination(self, hitInfo) -> Any: ...


class Sun(LightSource):
    def __init__(self, pos, state):
        self.position = pos
        self.state = state

    def calculate_illumination(self, hitInfo):
        # Get direction from intersection to light
        light_direction = self.position - hitInfo["intersection"]
        light_direction = light_direction / np.linalg.norm(light_direction)

        # Get normal, checking if we need to invert it (for two-sided objects)
        normal = hitInfo["normal"]
        incident_dot = np.dot(normal, light_direction)

        # If normal points away from ray, invert it
        if incident_dot < 0:
            normal = -normal
            incident_dot = -incident_dot

        # If surface is facing away from light, no illumination
        if incident_dot < 0:
            return np.zeros(3)

        # Calculate illumination using Lambert's law
        # illumination = object_color * light_color * (normal · light_direction)

        return hitInfo["sphere"].state["color"] * self.state["color"] * incident_dot


class Renderer:
    geometries: List[Geometry]

    def __init__(self):
        self.sRGB = True
        self.color = np.array([1, 1, 1])
        self.geometries: List[Geometry] = []
        self.lightSources: List[LightSource] = []

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

    def EmitRayFromIndex(self, maxWidthOrHeight, i, j):
        eye = [0, 0, 0]
        f = [0, 0, -1]
        r = [1, 0, 0]
        u = [0, 1, 0]
        s = [
            (2 * i - self.width) / maxWidthOrHeight,
            (self.height - 2 * j) / maxWidthOrHeight,
            0,
        ]

        s_x = s[0]  # 2*i - self.width/maxWidthOrHeight
        s_y = s[1]  # self.height - 2*j

        # Sum all terms
        ray_direction = np.add(np.add(f, np.multiply(s_x, r)), np.multiply(s_y, u))

        # This is equivalent to:
        ray_direction = [s_x, s_y, -1]
        # print(eye, ray_direction)
        return eye, ray_direction

    def Trace(self, position, direction):
        ray = {"position": np.array(position), "direction": np.array(direction)}
        hitInfo = self.CalculateRayCollision(ray)

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
            illumination = light.calculate_illumination(hitInfo)
            total_illumination += illumination

        return (
            int(total_illumination[0] * 255),
            int(total_illumination[1] * 255),
            int(total_illumination[2] * 255),
            255,
        )

    def CalculateRayCollision(self, ray):
        collisions = [
            g.calculate_intersection(ray["position"], ray["direction"])
            for g in self.geometries
        ]
        valid_collisions = [
            c for c in collisions if c is not None and c["distance"] > 0
        ]
        if valid_collisions:
            collision = min(valid_collisions, key=lambda x: x["distance"])

        else:
            collision = None

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


def parse_file(filename):
    image = None
    output_file = ""
    positions = []
    colors = []
    renderer = Renderer()
    with open(filename, "r") as file:
        for line in file:
            args = line.strip().split()
            if not args:
                continue

            keyword = args[0]
            rem = args[1::]
            if keyword == "png":
                width, height, output_file = int(rem[0]), int(rem[1]), rem[2]
                image = png(width, height)
                renderer = (
                    renderer.WithWidth(width)
                    .WithHeight(height)
                    .WithOutputFile(output_file)
                    .WithImage(image)
                )

            elif keyword == "color":
                c = np.array(rem).astype(float)
                renderer = renderer.SetColor(c)
            elif keyword == "sphere":
                r, xyz = float(rem[-1]), np.array(rem[0:-1]).astype(float)
                renderer = renderer.AddSphere(r, xyz)
            elif keyword == "sun":

                xyz = np.array(rem).astype(float)
                renderer = renderer.AddSun(xyz)

        renderer.RenderFrame()
        renderer.save()


# png width height
#   Always present in the input before any other keywords
#   width and height are positive integers
#   filename always ends .png
def png(width, height):
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    return image


def position(size, nums):
    """
    size is either 2, 3, or 4
    there are a size multiple of numbers after size (e.g. if size is 3 there will be 3 or 6 or 9 or 12 or … additional numbers)
    range x,y := [-1,1]
    """
    appending_tuple = []
    if size == 2:
        appending_tuple = [0, 1]
    elif size == 3:
        appending_tuple = [1]
    elif size == 4:
        appending_tuple = []
    else:
        return ValueError

    positions = [
        nums[i : i + size] + appending_tuple for i in range(0, len(nums), size)
    ]

    return positions


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


def dda(a, b, dim_index):
    """
    Where a,b := tuple(x,y,z,w,r,g,b,a,s,t)
    dim_index := which dimension should have integer coordinates

    returns list of integer points along line segment AB
    """

    points = []
    if a[dim_index] == b[dim_index]:
        return []

    if a[dim_index] > b[dim_index]:
        return dda(b, a, dim_index)

    delta = b - a
    delta_dim = delta[dim_index]

    s = delta / delta_dim
    e = np.ceil(a[dim_index]) - a[dim_index]
    o = e * s
    p = a + o

    counter = 0
    while p[dim_index] < b[dim_index]:
        points = points + [p]
        p = p + s
        counter += 1

    return points


def linear_to_srgb(linear):
    return np.where(
        linear < 0.0031308, linear * 12.92, 1.055 * (linear ** (1 / 2.4)) - 0.055
    )


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


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python program.py <input_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    parse_file(input_file)
