import numpy as np
from numpy.typing import NDArray
from ..structures import LightSource, HitInfo


class Sun(LightSource):
    def __init__(self, pos, state):
        self.position = pos
        self.direction = self.position / np.linalg.norm(self.position)
        self._state = state

    @property
    def state(self) -> dict:
        return self._state

    @state.setter
    def state(self, value: dict):
        self._state = value

    def calculate_illumination(self, hitInfo: HitInfo, debug: bool = False):
        if hitInfo.in_shadow.get(self, False):  # If this light source is blocked
            return np.zeros(3)

        # the sun is infinitely far away, the point doesn't matter
        light_direction = self.get_direction_from_point(hitInfo.point)

        normal = hitInfo.normal
        incident_dot = np.dot(normal, light_direction)

        if debug:
            print(normal, light_direction, incident_dot)

        # If surface is facing away from light, return black
        if incident_dot < 0:
            return np.zeros(3)

        # Make objects two-sided
        if incident_dot < 0:
            normal = -normal
            incident_dot = -incident_dot

        return hitInfo.color * self.state["color"] * incident_dot

    def get_direction_from_point(self, _: NDArray[np.float64]):
        return self.direction
