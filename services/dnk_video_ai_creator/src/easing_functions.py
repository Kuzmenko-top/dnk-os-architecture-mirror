# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/src/easing_functions.py"
# purpose: "Pure mathematical easing curves, Cubic Bezier, and Spring physics implementations."
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

"""
Deterministic easing functions for video animation keyframes.
Includes Bezier curves, polynomial easings, and analytical spring dynamics.
"""

import math
from typing import Callable, Dict, Optional
from .video_composition_schema import EasingType


def linear(t: float) -> float:
    """Linear progression."""
    return max(0.0, min(1.0, float(t)))


def quad_in(t: float) -> float:
    """Quadratic ease in."""
    t = linear(t)
    return t * t


def quad_out(t: float) -> float:
    """Quadratic ease out."""
    t = linear(t)
    return t * (2.0 - t)


def quad_in_out(t: float) -> float:
    """Quadratic ease in-out."""
    t = linear(t)
    if t < 0.5:
        return 2.0 * t * t
    return -1.0 + (4.0 - 2.0 * t) * t


def cubic_in(t: float) -> float:
    """Cubic ease in."""
    t = linear(t)
    return t * t * t


def cubic_out(t: float) -> float:
    """Cubic ease out."""
    t = linear(t)
    f = t - 1.0
    return f * f * f + 1.0


def cubic_in_out(t: float) -> float:
    """Cubic ease in-out."""
    t = linear(t)
    if t < 0.5:
        return 4.0 * t * t * t
    f = 2.0 * t - 2.0
    return 0.5 * f * f * f + 1.0


def cubic_bezier(t: float, x1: float = 0.25, y1: float = 0.1, x2: float = 0.25, y2: float = 1.0) -> float:
    """
    Cubic Bezier curve evaluator using Newton-Raphson and binary subdivision.
    Maps progress t in [0, 1] to bezier y output.
    """
    t = linear(t)
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0

    # Polynomial coefficients for B(u) = 3*u*(1-u)^2*P1 + 3*u^2*(1-u)*P2 + u^3
    # B_x(u) = 3*x1*u*(1-u)^2 + 3*x2*u^2*(1-u) + u^3
    def sample_curve_x(u: float) -> float:
        return ((3.0 * x1 * (1.0 - u) + 3.0 * x2 * u) * (1.0 - u) + u) * u

    def sample_curve_y(u: float) -> float:
        return ((3.0 * y1 * (1.0 - u) + 3.0 * y2 * u) * (1.0 - u) + u) * u

    def sample_curve_derivative_x(u: float) -> float:
        return 3.0 * (1.0 - 3.0 * x2 + 3.0 * x1) * u * u + 2.0 * (3.0 * x2 - 6.0 * x1) * u + 3.0 * x1

    # Solve sample_curve_x(u) = t for u
    u_guess = t
    for _ in range(8):
        x_val = sample_curve_x(u_guess) - t
        if abs(x_val) < 1e-6:
            break
        d_x = sample_curve_derivative_x(u_guess)
        if abs(d_x) < 1e-6:
            break
        u_guess -= x_val / d_x

    # Binary search fallback if Newton-Raphson bounds breached
    if u_guess < 0.0 or u_guess > 1.0:
        u_lower, u_upper = 0.0, 1.0
        u_guess = t
        for _ in range(12):
            x_val = sample_curve_x(u_guess)
            if abs(x_val - t) < 1e-6:
                break
            if x_val > t:
                u_upper = u_guess
            else:
                u_lower = u_guess
            u_guess = 0.5 * (u_lower + u_upper)

    return sample_curve_y(max(0.0, min(1.0, u_guess)))


def spring(t: float, stiffness: float = 100.0, damping: float = 10.0, mass: float = 1.0) -> float:
    """
    Analytical spring physics easing function.
    Solves damped harmonic oscillator equation from 0.0 to 1.0 over time t in [0, 1].
    """
    t = linear(t)
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0

    stiffness = max(1.0, float(stiffness))
    damping = max(0.1, float(damping))
    mass = max(0.1, float(mass))

    w0 = math.sqrt(stiffness / mass)
    zeta = damping / (2.0 * math.sqrt(stiffness * mass))

    if zeta < 1.0:
        # Underdamped
        wd = w0 * math.sqrt(1.0 - zeta * zeta)
        decay = math.exp(-zeta * w0 * t * 4.0)
        envelope = math.cos(wd * t * 4.0) + (zeta * w0 / wd) * math.sin(wd * t * 4.0)
        return 1.0 - decay * envelope
    elif abs(zeta - 1.0) < 1e-5:
        # Critically damped
        decay = math.exp(-w0 * t * 4.0)
        return 1.0 - decay * (1.0 + w0 * t * 4.0)
    else:
        # Overdamped
        r1 = -w0 * (zeta - math.sqrt(zeta * zeta - 1.0))
        r2 = -w0 * (zeta + math.sqrt(zeta * zeta - 1.0))
        return 1.0 - (r2 * math.exp(r1 * t * 4.0) - r1 * math.exp(r2 * t * 4.0)) / (r2 - r1)


EASING_REGISTRY: Dict[EasingType, Callable[[float], float]] = {
    EasingType.LINEAR: linear,
    EasingType.EASE_IN: quad_in,
    EasingType.EASE_OUT: quad_out,
    EasingType.EASE_IN_OUT: quad_in_out,
    EasingType.QUAD_IN: quad_in,
    EasingType.QUAD_OUT: quad_out,
    EasingType.QUAD_IN_OUT: quad_in_out,
    EasingType.CUBIC_IN: cubic_in,
    EasingType.CUBIC_OUT: cubic_out,
    EasingType.CUBIC_IN_OUT: cubic_in_out,
}


def get_easing_function(easing_type: EasingType) -> Callable[[float], float]:
    """Retrieve easing function callable by EasingType enum."""
    return EASING_REGISTRY.get(easing_type, linear)


def evaluate_easing(easing_type: EasingType, t: float, params: Optional[Dict[str, float]] = None) -> float:
    """Evaluate easing progress at progress t with optional parameter overrides."""
    if easing_type == EasingType.BEZIER:
        p = params or {}
        return cubic_bezier(
            t,
            x1=p.get("x1", 0.25),
            y1=p.get("y1", 0.1),
            x2=p.get("x2", 0.25),
            y2=p.get("y2", 1.0),
        )
    elif easing_type == EasingType.SPRING:
        p = params or {}
        return spring(
            t,
            stiffness=p.get("stiffness", 100.0),
            damping=p.get("damping", 10.0),
            mass=p.get("mass", 1.0),
        )

    fn = get_easing_function(easing_type)
    return fn(t)
