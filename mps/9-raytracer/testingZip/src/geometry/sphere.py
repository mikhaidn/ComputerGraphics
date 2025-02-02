import numpy as np

from texure_handler import get_texture_color
from ..structures import Geometry, HitInfo, Ray
from numpy.typing import NDArray


class Sphere(Geometry):
    r: float
    position: NDArray[np.float64]

    def __init__(self, r, pos, state):
        self.r = r
        self.position = np.array(pos)
        self._state = state

    @property
    def state(self) -> dict:
        return self._state

    @state.setter
    def state(self, value: dict):
        self._state = value

    def calculate_intersection(self, ray: Ray) -> HitInfo:
        # Mapping variables to the algorithm notation
        r_o = ray.origin
        r_d = ray.direction
        c = self.position
        r = self.r

        # 1. Check if origin is inside sphere
        c_minus_ro = c - r_o
        inside = np.dot(c_minus_ro, c_minus_ro) < r * r

        # 2. Calculate t
        t_c = np.dot(c_minus_ro, r_d) / np.dot(r_d, r_d)

        # 3. Early exit check
        if not inside and t_c < 0:
            return None

        # 4. Calculate distance norm
        closest_point = r_o + t_c * r_d - c
        d_squared = np.dot(closest_point, closest_point)

        # 5. Early exit check
        if not inside and r * r < d_squared:
            return None

        # 6. Calculate t_offset
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
        if np.dot(normal, ray.direction) > 0:
            normal = -normal

        hit = HitInfo()
        hit.distance = t
        hit.point = intersection
        hit.normal = normal
        hit.material = self
        hit.incident_direction = ray.direction
        hit.color = self.getColor(hit.point)
        hit.shininess = self.state["shininess"]
        hit.refraction_index = self.state["ior"]
        hit.transparency = self.state["transparency"]
        hit.roughness = self.state["roughness"]

        hit.add_noise_to_normal(hit.roughness)

        return hit

    def getColor(self, point: NDArray[np.float64]):
        texture = self.state["texture"]
        if texture is not None:
            # Get point relative to sphere center
            x, y, z = point - self.position

            # Longitude: angle in xz plane from x axis
            longitude = np.arctan2(x, z) - np.pi / 2  # swap x and z
            u = ((longitude + np.pi) / (2 * np.pi)) % 1

            # Latitude: angle from y axis
            latitude = np.arccos(y / self.r)
            v = latitude / np.pi

            return get_texture_color(texture, u, v)
        return self.state["color"]
