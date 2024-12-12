import numpy as np

from src.geometry.plane import Plane
from texure_handler import get_texture_color
from ..structures import Geometry, HitInfo, Ray, Vertex
from numpy.typing import NDArray


class Triangle(Plane):
    point: NDArray[np.float64]
    normal: NDArray[np.float64]

    v0: Vertex
    v1: Vertex
    v2: Vertex

    def __init__(self, v0: Vertex, v1: Vertex, v2: Vertex, state):
        self.v0 = v0
        self.v1 = v1
        self.v2 = v2

        # Calculate normal using cross product
        edge1 = self.v1.point - self.v0.point
        edge2 = self.v2.point - self.v0.point
        self.normal = np.cross(edge1, edge2)
        self.normal = self.normal / np.linalg.norm(self.normal)  # normalize

        # Calculate a1 and a2 vectors as shown in equations
        # a1 = p2 - p0 × n
        # a2 = p1 - p0 × n
        self.a1 = np.cross(self.v2.point - self.v0.point, self.normal)  # p2 - p0
        self.a2 = np.cross(self.v1.point - self.v0.point, self.normal)  # p1 - p0

        # Calculate e1 and e2 vectors
        # e1 = (1 / (a1 · (p1 - p0))) * a1
        # e2 = (1 / (a2 · (p2 - p0))) * a2
        self.e1 = self.a1 / np.dot(self.a1, self.v1.point - self.v0.point)  # p1 - p0
        self.e2 = self.a2 / np.dot(self.a2, self.v2.point - self.v0.point)  # p2 - p0

        self.point = self.v0.point

        self._state = state

    @property
    def state(self) -> dict:
        return self._state

    @state.setter
    def state(self, value: dict):
        self._state = value

    def calculate_intersection(self, ray: Ray) -> HitInfo:
        plane_hit = super().calculate_intersection(ray)
        if plane_hit is None:
            return None

        # if Ray is not None:
        #     return plane_hit

        # plane intersection point from superclass call of Plane
        p = plane_hit.point

        # Calculate barycentric coordinates using precomputed e vectors
        # b1 = e1 · (p - p0)
        # b2 = e2 · (p - p0)
        # b0 = 1 - b1 - b2
        b1 = np.dot(self.e1, (p - self.v0.point))
        b2 = np.dot(self.e2, (p - self.v0.point))
        b0 = 1 - b1 - b2

        # Point is inside triangle if all barycentric coordinates are between 0 and 1
        if b0 < 0 or b1 < 0 or b2 < 0:
            return None

        texture = self.state["texture"]
        if texture is None:
            plane_hit.color = self.state["color"]
            return plane_hit
        c0 = get_texture_color(texture, self.v0.texcoord[0], self.v0.texcoord[1])
        c1 = get_texture_color(texture, self.v1.texcoord[0], self.v1.texcoord[1])
        c2 = get_texture_color(texture, self.v2.texcoord[0], self.v2.texcoord[1])

        barys = np.array([b0, b1, b2])
        colors = np.array([c0, c1, c2])
        color = np.dot(barys, colors)

        plane_hit.color = color
        return plane_hit
