from PIL import Image
import sys


def parse_file(filename):
    image = None
    positions = []
    colors = []

    with open(filename, "r") as file:
        for line in file:
            parts = line.strip().split()
            if not parts:
                continue

            keyword = parts[0]
            bufferIndex = 1
            bufferSize = int(parts[bufferIndex])

            if keyword == "png":
                width, height, output_file = int(parts[1]), int(parts[2]), parts[3]
                image = Image.new("RGBA", (width, height), (0, 0, 0, 0))

            elif keyword == "position":
                if bufferSize != 2:
                    break
                positions = [
                    (int(parts[i]), int(parts[i + 1]))
                    for i in range(bufferIndex+1, len(parts), bufferSize)
                ]

            elif keyword == "color":
                if bufferSize != 4:
                    break
                colors = [
                    (
                        int(parts[i]),
                        int(parts[i + 1]),
                        int(parts[i + 2]),
                        int(parts[i + 3]),
                    )
                    for i in range(bufferIndex+1, len(parts), bufferSize)
                ]

            elif keyword == "drawPixels":
                for i in range(bufferSize):
                    if i < len(positions) and i < len(colors):
                        x, y = positions[i]
                        image.putpixel((x, y), colors[i])

    if image:
        image.save(output_file)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python program.py <input_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    parse_file(input_file)
