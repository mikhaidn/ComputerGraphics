import numpy as np
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
      

    def calculate_intersection(self, ray:Ray) -> HitInfo:
        # For clarity, let's map variables to the algorithm notation
        r_o = ray.origin  # ray origin
        r_d = ray.direction  # ray direction
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

        hit = HitInfo()
        hit.distance = t
        hit.point = intersection
        hit.normal = normal
        hit.material = self
        return hit
