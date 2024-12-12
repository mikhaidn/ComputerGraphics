import numpy as np
from ..structures import Geometry, HitInfo, Ray
from numpy.typing import NDArray


class Plane(Geometry):
    point: NDArray[np.float64]
    normal: NDArray[np.float64]

    def __init__(self, abcd, state):
        n = abcd[0:3]
        self.normal = n / np.linalg.norm(n)
        a = abcd[0]
        b = abcd[1]
        c = abcd[2]
        d = abcd[3]

        self.point = self.getNonZeroPoint(a, b, c, d)
        self._state = state

    @property
    def state(self) -> dict:
        return self._state

    @state.setter
    def state(self, value: dict):
        self._state = value

    def calculate_intersection(self, ray: Ray) -> HitInfo:
        # Mapping variables to the algorithm notation
        r_o = ray.origin  # ray origin
        r_d = ray.direction  # ray direction
        p = self.point
        n = self.normal

        dot_product = np.dot(r_d, n)

        if dot_product == 0:
            return None

        t = np.dot((p - r_o), n) / np.dot(r_d, n)
        if t < 0:
            return None

        intersection = t * r_d + r_o

        hit = HitInfo()
        hit.distance = t
        hit.point = intersection
        hit.normal = -n if np.dot(r_d, n) > 0 else n
        hit.color = self.state["color"]
        hit.material = self
        return hit

    def getNonZeroPoint(self, a, b, c, d):
        if d == 0:
            return np.array([0, 0, 0])
        if a != 0:
            return np.array([-d / a, 0, 0])
        if b != 0:
            return np.array([0, -d / b, 0])
        if c != 0:
            return np.array([0, 0, -d / c])
        raise AttributeError("Invalid Plane", a, b, c, d)
