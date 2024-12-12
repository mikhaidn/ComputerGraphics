from typing import TypeVar, Protocol, List
import numpy as np
from numpy.typing import NDArray


class Ray:
    origin: NDArray[np.float64]
    direction: NDArray[np.float64]

class HitInfo:
    distance: float
    normal: List[float]
    point: List[float]
    material: "Geometry"      

class Geometry(Protocol):
    def calculate_intersection(self, ray:Ray) -> HitInfo: ...

    @property 
    def state(self) -> dict: ...


class LightSource(Protocol):
    def calculate_illumination(self, hitInfo:HitInfo) -> List[float]: ...

    @property 
    def state(self) -> dict: ...
