from PIL import Image
import sys
import numpy as np
from numpy.typing import NDArray


def load_texture(filename: str) -> NDArray:
    """
    Load image file as numpy array, converting from sRGB to linear RGB
    """
    img = Image.open(filename)
    texture = np.array(img, dtype=np.float32) / 255.0  # Normalize to [0,1]

    if texture.shape[-1] == 4:  # If RGBA
        texture = texture[..., :3]  # Take only RGB channels

    # Convert sRGB to linear RGB
    return np.where(
        texture <= 0.04045, texture / 12.92, ((texture + 0.055) / 1.055) ** 2.4
    )


def get_texture_color(texture: np.ndarray, u: float, v: float) -> NDArray:
    """
    Sample texture at given UV coordinates
    u,v should be in range [0,1]
    Returns RGB color as numpy array
    """
    # Get texture dimensions
    height, width = texture.shape[:2]

    x = int(u * (width - 1))
    y = int(v * (height - 1))

    # Return color at that pixel, ignore A
    return texture[y, x]
