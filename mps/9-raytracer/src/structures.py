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
    shininess: NDArray[np.float64]
    refraction_index: float
    roughness: float
    transparency: NDArray[np.float64]
    material: "Geometry"  # never really used this lol
    incident_direction: NDArray[np.float64]
    in_shadow: dict

    def __str__(self):
        return f"Hit:\n    dist={self.distance:.3f}\n    normal={self.normal}\n    point={self.point} \n material:{self.material}"

    def add_noise_to_normal(self, sigma):
        if sigma == 0:
            return
        # Generate three random numbers with standard deviation sigma
        noise = np.random.normal(0, sigma, 3)

        # Add noise to the normal vector
        noisy_normal = self.normal + noise

        # Normalize the result to ensure it remains a unit vector
        self.normal = noisy_normal / np.linalg.norm(noisy_normal)


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
