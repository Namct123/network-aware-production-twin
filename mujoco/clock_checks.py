"""Inclusive elapsed-time checks with a 1 ns numerical tolerance, not clock calibration."""
import math


def elapsed_at_least(now, previous, duration):
    elapsed = now-previous
    # Floating-point integration can miss an exact threshold by a few ulps.
    # A 1 ns early stop is conservative; no physical timing parameter is fitted.
    return elapsed >= duration or math.isclose(elapsed,duration,rel_tol=0.,abs_tol=1e-9)
