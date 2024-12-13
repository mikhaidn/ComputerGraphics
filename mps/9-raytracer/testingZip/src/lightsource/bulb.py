import numpy as np
from numpy.typing import NDArray
from ..structures import LightSource, HitInfo


class Bulb(LightSource):
    def __init__(self, pos, state):
        self.position = pos
        self._state = state

    @property
    def state(self) -> dict:
        return self._state

    @state.setter
    def state(self, value: dict):
        self._state = value

    def calculate_illumination(self, hitInfo: HitInfo, debug: bool = False):

        vector = self.position - hitInfo.point
        distance = np.linalg.norm(vector)
        direction = vector / distance

        # If shadow intersection is further than light, ignore it
        if hitInfo.in_shadow.get(self, False):
            shadow_distance = hitInfo.in_shadow.get(self)
            if shadow_distance <= distance:
                # Object is in shadow
                return np.zeros(3)

        normal = hitInfo.normal
        incident_dot = np.dot(normal, direction)

        if debug:
            print(normal, direction, incident_dot)

        # If surface is facing away from light, return black
        if incident_dot < 0:
            return np.zeros(3)

        # Make objects two-sided
        if incident_dot < 0:
            normal = -normal
            incident_dot = -incident_dot

        # Calculate light via inverse square
        intensity = 1.0 / (distance**2)

        # Combine colors, angle, and intensity
        return hitInfo.color * self.state["color"] * incident_dot * intensity

    def get_direction_from_point(self, point: NDArray[np.float64]):
        vector = self.position - point
        distance = np.linalg.norm(vector)
        direction = vector / distance

        return direction
