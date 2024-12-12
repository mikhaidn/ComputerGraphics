from typing import TypeVar, Protocol, List
import numpy as np
from numpy.typing import NDArray


class Vertex:
    point: NDArray[np.float64]
    texcoord: tuple


class Ray:
    origin: NDArray[np.float64]
    direction: NDArray[np.float64]

    def __str__(self):
        return f"Ray: \n    origin={self.origin}\n    direction={self.direction}"


class HitInfo:
    distance: float
    normal: List[float]
    point: List[float]
    color: NDArray[np.float64]
    material: "Geometry"
    in_shadow: dict

    def __str__(self):
        return f"Hit:\n    dist={self.distance:.3f}\n    normal={self.normal}\n    point={self.point} \n material:{self.material}"


class Geometry(Protocol):
    def calculate_intersection(self, ray: Ray) -> HitInfo: ...

    @property
    def state(self) -> dict: ...


class LightSource(Protocol):
    def calculate_illumination(self, hitInfo: HitInfo) -> NDArray[np.float64]: ...

    def get_direction_from_point(
        self, point: NDArray[np.float64]
    ) -> NDArray[np.float64]: ...

    @property
    def state(self) -> dict: ...
