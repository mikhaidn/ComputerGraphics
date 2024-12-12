import numpy as np
from typing import List
from .structures import Ray,Geometry, HitInfo
class BoundingBox:
    def __init__(self, min_point=None, max_point=None):
        self.min_point = np.array([-np.inf, -np.inf, -np.inf]) if min_point is None else np.array(min_point)
        self.max_point = np.array([np.inf, np.inf, np.inf]) if max_point is None else np.array(max_point)

    def intersect(self, ray: Ray) -> bool:
        # Ray-AABB intersection test
        t_min = (self.min_point - ray.origin) / ray.direction
        t_max = (self.max_point - ray.origin) / ray.direction
        
        t1 = np.minimum(t_min, t_max)
        t2 = np.maximum(t_min, t_max)
        
        t_near = np.max(t1)
        t_far = np.min(t2)
        
        return t_far >= t_near and t_far > 0

class BVHNode:
    def __init__(self, geometries:  List[Geometry], axis=0):
        self.bbox = self.compute_bounds(geometries)
        self.left = None
        self.right = None
        self.geometry = None
        
        if len(geometries) == 1:
            self.geometry = geometries[0]
            return
            
        # Sort geometries by center along current axis
        geometries.sort(key=lambda g: g.position[axis])
        mid = len(geometries) // 2
        
        # Recursively build tree
        self.left = BVHNode(geometries[:mid], (axis + 1) % 3)
        self.right = BVHNode(geometries[mid:], (axis + 1) % 3)
    
    def compute_bounds(self, geometries:  List[Geometry]):
        if not geometries:
            return BoundingBox()
            
        min_point = np.array([np.inf, np.inf, np.inf])
        max_point = np.array([-np.inf, -np.inf, -np.inf])
        
        for g in geometries:
            # For sphere
            min_point = np.minimum(min_point, g.position - g.r)
            max_point = np.maximum(max_point, g.position + g.r)
            
        return BoundingBox(min_point, max_point)

    def intersect(self, ray: Ray)-> HitInfo|None:
        if not self.bbox.intersect(ray):
            return None
            
        if self.geometry:
            return self.geometry.calculate_intersection(ray)
            
        left_hit = self.left.intersect(ray) if self.left else None
        right_hit = self.right.intersect(ray) if self.right else None
        
        if not left_hit:
            return right_hit
        if not right_hit:
            return left_hit
            
        return left_hit if left_hit.distance < right_hit.distance else right_hit