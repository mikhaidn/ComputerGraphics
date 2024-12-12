import numpy as np
from ..structures import LightSource, HitInfo


class Sun(LightSource):
    def __init__(self, pos, state):
        self.position = pos
        self._state = state

    @property
    def state(self) -> dict:
        return self._state
        
    @state.setter
    def state(self, value: dict):
        self._state = value

    def calculate_illumination(self, hitInfo:HitInfo):
        # Get direction from intersection to light
        light_direction = self.position - hitInfo.point
        light_direction = light_direction / np.linalg.norm(light_direction)

        # Get normal, checking if we need to invert it (for two-sided objects)
        normal = hitInfo.normal
        incident_dot = np.dot(normal, light_direction)

        # # If normal points away from ray, invert it
        # if incident_dot < 0:
        #     normal = -normal
        #     incident_dot = -incident_dot

        # If surface is facing away from light, no illumination
        if incident_dot < 0:
            return np.zeros(3)

        # Calculate illumination using Lambert's law
        # illumination = object_color * light_color * (normal · light_direction)

        print(hitInfo.material.state["color"])
        print(self.state["color"])
        return hitInfo.material.state["color"] * self.state["color"] * incident_dot
