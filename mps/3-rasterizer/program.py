from PIL import Image
import sys
import numpy as np


class Renderer:

    def _init__(self):
        return self

    def WithHyp(self, b):
        self.hyp = b
        return self

    def WithDepth(self, b):
        self.depthDict = {}
        self.depth = b
        return self

    def WithSRGB(self, b):
        self.sRGB = b
        return self

    def WithWidth(self, width):
        self.width = width
        return self

    def WithHeight(self, height):
        self.height = height
        return self

    def WithOutputFile(self, output_file):
        self.output_file = output_file
        return self

    def WithPositions(self, positions):
        positions = np.asarray(positions)
        self.positions = positions
        return self

    def WithColors(self, colors):
        self.colors = np.asarray(colors)
        return self

    def WithElements(self, elements):
        self.elements = np.asarray(elements)
        return self

    def WithImage(self, image):
        self.image = image
        return self

    def flattenBuffers(self):
        return

    def save(self):
        if self.sRGB:
            srgb_image = convert_linear_to_srgb(self.image)
            self.image = srgb_image
        self.image.save(self.output_file)

    def drawArraysTriangles(self, first, count):
        if count % 3 != 0:
            raise ValueError("Count must be a multiple of 3")

        print(first, count)
        flattenedBuffers = np.hstack((self.positions, self.colors))

        for i in range(0, count, 3):
            # Get indices for the current triangle
            p = flattenedBuffers[first + i]
            q = flattenedBuffers[first + i + 1]
            r = flattenedBuffers[first + i + 2]

            self.scanline(p, q, r)
        # Save the image
        self.image.save(self.output_file)

        return self.image

    def drawElementsTriangles(self, count, offset):

        print(count, offset)
        flattenedBuffers = np.hstack((self.positions, self.colors))
        print(flattenedBuffers.shape, flattenedBuffers)
        print(self.elements, len(self.elements))
        for i in range(0, count, 3):
            # Get indices for the current triangle
            p = flattenedBuffers[self.elements[offset + i]]
            q = flattenedBuffers[self.elements[offset + i + 1]]
            r = flattenedBuffers[self.elements[offset + i + 2]]

            self.scanline(p, q, r)
        # Save the image
        self.image.save(self.output_file)

        return self.image

    def scanline(self, p, q, r, y_index=1, x_index=0):
        """
        Where p,q,r approx:= tuple(x,y,z,w,r,g,b,a,s,t)
        y_index := which dimension should have y coordinates
        """
        # Convert points to numpy array
        points = np.array([p, q, r])
        # Divide everything by w
        w = points[:, 3:4]

        if self.hyp:
            points = points / w
        else:
            points[:, 0:3] = points[:, 0:3] / w
        points[:, 3:4] = 1 / w
        # Viewport transformation

        xy = points[:, 0:2]
        xy = (xy + 1) * np.array([self.width, self.height]) / 2
        points[:, :2] = xy

        # Sort points based on y-coordinate (ascending order)
        sorted_indices = np.argsort(points[:, y_index])
        sorted_points = points[sorted_indices]

        # Assign top, middle, bottom
        b, m, t = sorted_points

        plong = dda(b, t, y_index)
        ptop = dda(m, t, y_index)
        pbot = dda(b, m, y_index)

        try:
            pother = pbot + ptop
        except:
            print(ptop, pbot)
            raise Exception

        if len(plong) == 0:
            return plong

        for i in range(len(plong)):
            left, right = plong[i], pother[i]
            points_to_plot = dda(left, right, x_index)
            self.plotPoints(points_to_plot)

    def plotPoints(self, points, color_override=None):
        if len(points) == 0:
            return
        [self.plotPoint(point, color_override) for point in points]

    def plotPoint(self, point, color_override=None):
        if len(point) == 0:
            return
        w = point[3]
        xy = tuple(np.asarray((point[0:2])).astype(int))
        z = point[2]
        if self.hyp:
            carray = point[4:8] / w
        else:
            carray = point[4:8]
        colors = tuple(np.asarray(carray * 256).astype(int))
        if color_override:
            colors = color_override

        if self.depth:
            if xy not in self.depthDict or self.depthDict[xy] > z:
                self.depthDict[xy] = z
            else:
                return
        try:
            self.image.putpixel(xy, colors)
        except:
            print(xy, colors, w, point)
            return BufferError


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
                    renderer.WithHyp(False)
                    .WithDepth(False)
                    .WithSRGB(False)
                    .WithWidth(width)
                    .WithHeight(height)
                    .WithOutputFile(output_file)
                    .WithImage(image)
                )

            elif keyword == "depth":
                renderer = renderer.WithDepth(True)

            elif keyword == "sRGB":
                renderer = renderer.WithSRGB(True)

            elif keyword == "hyp":
                renderer = renderer.WithHyp(True)

            elif keyword == "position":
                size, nums = int(rem[0]), [float(n) for n in rem[1:]]
                positions = position(size, nums)
                renderer = renderer.WithPositions(positions)

            elif keyword == "color":
                size, nums = int(rem[0]), [float(n) for n in rem[1:]]
                colors = color(size, nums)
                renderer = renderer.WithColors(colors)

            elif keyword == "elements":
                elements = [int(n) for n in rem]
                renderer = renderer.WithElements(elements)

            elif keyword == "drawArraysTriangles":
                first, count = int(rem[0]), int(rem[1])
                image = renderer.drawArraysTriangles(first, count)

            elif keyword == "drawElementsTriangles":
                count, offset = int(rem[0]), int(rem[1])
                image = renderer.drawElementsTriangles(count, offset)
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
