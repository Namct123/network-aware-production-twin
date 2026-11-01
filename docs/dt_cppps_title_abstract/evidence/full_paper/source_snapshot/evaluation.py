"""Evaluator owns ground truth; no method here supplies data to the controller."""

import math


class Evaluator:
    def __init__(self, geometry):
        self.geometry = geometry
        self.errors = []

    def observe(self, estimate, truth, before_phase):
        if before_phase not in {"TRACK", "ALIGN"} or estimate.reason != "tracking":
            return None
        error = estimate.y_m-truth["product_xyz_m"][1]
        self.errors.append(error)
        return error

    def finish(self, truth, phase, bin_number):
        x,y,z = truth["product_xyz_m"]
        g = self.geometry
        placed = supported = None
        if phase == "DONE":
            bx,by = g["bin_centers_xy_m"][bin_number-1]
            tx,ty = ((a-b)/2 for a,b in zip(g["bin_inner_size_xy_m"],g["product_size_m"][:2]))
            placed = abs(x-bx) < tx and abs(y-by) < ty and g["placement_z_m"][0] < z < g["placement_z_m"][1]
        elif phase == "HOLD":
            margin = g["product_size_m"][1]/2
            long_supported = (abs(x-g["lane_x_m"]) < g["hold_lane_tolerance_m"]
                         and g["long_belt_y_m"][0] < y < g["long_belt_y_m"][1]-margin
                         )
            front_supported = all(bounds[0]+size/2 < q < bounds[1]-size/2
                                  for bounds,size,q in zip(g["front_belt_xy_m"],g["product_size_m"][:2],(x,y)))
            supported = (long_supported or front_supported) and g["hold_z_m"][0] < z < g["hold_z_m"][1]
        absolute = sorted(abs(e) for e in self.errors)
        return {"placement_pass_evaluator_only": placed,
                "hold_product_supported_evaluator_only": supported,
                "y_error_samples": len(self.errors),
                "y_error_rmse_m": math.sqrt(sum(e*e for e in self.errors)/len(self.errors)) if self.errors else None,
                "y_error_p95_abs_m": absolute[math.ceil(.95*len(absolute))-1] if absolute else None,
                "y_error_max_abs_m": max(absolute) if absolute else None}
