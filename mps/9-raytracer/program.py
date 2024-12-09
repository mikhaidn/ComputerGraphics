from PIL import Image
import sys
import numpy as np
from typing import List


class Geometry:
    def intersection(self, origin, direction):
        raise NotImplementedError()


class Sphere(Geometry):
    def __init__(self, r, pos, state):
        self.r = r
        self.position = pos
        self.state = state

    def calculate_intersection(self, origin, direction):
        print(
            "i'm raytracing to Sphere!",
            origin,
            direction,
            self.position,
            self.r,
            self.state,
        )


class Sun(Geometry):
    def __init__(self, pos, state):
        self.position = pos
        self.state = state

    def calculate_intersection(self, origin, direction):
        print(
            "i'm raytracing to Sun!",
            origin,
            direction,
            self.position,
            self.state,
        )


class Renderer:

    def __init__(self):
        self.sRGB = True
        self.color = [0, 0, 0]
        self.geometries: List[Geometry] = []

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
        self.geometries.append(sun)
        return self

    def SetColor(self, rgb):
        self.color = rgb
        return self

    def GetStates(self):
        states = {}
        states["color"] = self.color

        return states

    def save(self):
        [g.calculate_intersection(None, None) for g in self.geometries]
        print(self.image, self.height, self.width, self.output_file)

        if self.sRGB:
            srgb_image = convert_linear_to_srgb(self.image)
            self.image = srgb_image
        # self.image.save(self.output_file)


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
