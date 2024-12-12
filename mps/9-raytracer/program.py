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

        renderer.RenderFrame()
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
