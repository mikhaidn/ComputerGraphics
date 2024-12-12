from PIL import Image
import sys
import numpy as np
from src.renderer import Renderer


def parse_file(filename):
    image = None
    output_file = ""
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

            elif keyword == "expose":
                renderer = renderer.WithExposure(float(rem[0]))

            elif keyword == "up":
                xyz = np.array(rem).astype(float)
                renderer = renderer.SetUp(xyz)

            elif keyword == "eye":
                xyz = np.array(rem).astype(float)
                renderer = renderer.SetEye(xyz)

            elif keyword == "forward":
                xyz = np.array(rem).astype(float)
                renderer = renderer.SetForward(xyz)

            elif keyword == "fisheye":
                renderer = renderer.SetFisheye()

            elif keyword == "panorama":
                renderer = renderer.SetPanorama()

            elif keyword == "plane":
                abcd = np.array(rem).astype(float)
                renderer = renderer.AddPlane(abcd)

            elif keyword == "xyz":
                xyz = np.array(rem).astype(float)
                renderer = renderer.AddVertex(xyz)

            elif keyword == "tri":
                idx = np.array(rem).astype(int)

                renderer = renderer.AddTriangle(idx)

            elif keyword == "texture":
                renderer = renderer.SetTexture(rem[0])

            elif keyword == "texcoord":
                uv = np.array(rem).astype(float)
                renderer = renderer.SetTexcoord(uv)

            elif keyword == "bulb":
                xyz = np.array(rem).astype(float)

                renderer = renderer.AddBulb(xyz)

            elif keyword == "shininess":
                renderer = renderer.SetPanorama()

            elif keyword == "bounces":
                renderer = renderer.SetPanorama()

            elif keyword == "transparency":
                renderer = renderer.SetPanorama()

            elif keyword == "ior":
                renderer = renderer.SetPanorama()

            elif keyword == "roughness":
                renderer = renderer.SetPanorama()

            elif keyword == "aa":
                renderer = renderer.SetPanorama()

            elif keyword == "dof":
                renderer = renderer.SetPanorama()

            elif keyword == "gi":
                renderer = renderer.SetPanorama()

        renderer.RenderFrame()
        renderer.PostProcess()
        renderer.save()


# png width height
#   Always present in the input before any other keywords
#   width and height are positive integers
#   filename always ends .png
def png(width, height):
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    return image


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python program.py <input_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    parse_file(input_file)
