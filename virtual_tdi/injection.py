from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from math import pi, sqrt

from .models import Fuel
from .hydraulics import NozzleConfig, VP37HydraulicConfig, NeedleConfig
from .vp37_cam import VP37CamProfile

@dataclass
class InjectionLineConfig:
    length_m: float = 0.4
    diameter_mm: float = 1.5
    segments: int = 5 # Increased segments for better wave representation

@dataclass
class InjectionResult:
    """High-resolution result of a single injection event simulation."""
    time_s: np.ndarray
    line_pressure_pa: np.ndarray # Pressure at the injector
    needle_lift_m: np.ndarray
    mdot_fuel_kg_s: np.ndarray

def solve_injection_hydraulics(
    cam: VP37CamProfile,
    *,
    rpm: float,
    iq_mg: float,
    fuel: Fuel,
    nozzle: NozzleConfig,
    needle: NeedleConfig,
    hyd: VP37HydraulicConfig,
    line: InjectionLineConfig,
    p_cylinder_pa: float,
    cylinder: int = 1,
) -> InjectionResult:
    """
    Solves the 1D injection hydraulics including a lumped-parameter line model
    and dynamic needle lift.
    """
    duration_main_deg = cam.duration_main_crank_deg(
        iq_mg_per_stroke=iq_mg, cylinder=cylinder, iq_max_mg=51.0, delivery_start_frac=0.4
    )
    if duration_main_deg <= 0.0: return InjectionResult(np.array([]), np.array([]), np.array([]), np.array([]))

    a_deg, s_mm = cam._rising_segment(cam._lobe_index_for_cylinder(cylinder))
    if a_deg.size < 2: return InjectionResult(np.array([]), np.array([]), np.array([]), np.array([]))

    dur_pump_deg = max(0.0, duration_main_deg / 2.0)
    a_start, a_end = float(a_deg[0]), min(float(a_deg[-1]), float(a_deg[0]) + dur_pump_deg)
    mask = (a_deg >= a_start) & (a_deg <= a_end)
    a_deg, s_mm = a_deg[mask], s_mm[mask]
    if a_deg.size < 2: return InjectionResult(np.array([]), np.array([]), np.array([]), np.array([]))

    omega_pump = (rpm / 2.0) * 2.0 * pi / 60.0
    total_time = (a_deg[-1] - a_deg[0]) * pi / 180.0 / omega_pump
    dt = 5e-8 # Smaller time step for stability with needle dynamics
    n_steps = int(total_time / dt)
    time_s = np.linspace(0, total_time, n_steps)

    L_seg, A_line, V_seg = line.length_m / line.segments, pi * (line.diameter_mm*1e-3)**2 / 4.0, (pi * (line.diameter_mm*1e-3)**2 / 4.0) * (line.length_m / line.segments)
    rho, K = fuel.density_kg_per_m3, fuel.bulk_modulus_pa
    
    # State: [p_1, q_1, ... p_N, q_N, x_needle, v_needle]
    N = line.segments
    state = np.zeros(2 * N + 2)
    p_back = p_cylinder_pa
    state[::2] = p_back 

    pump_angle_rad = np.interp(time_s, (time_s[0], time_s[-1]), (a_deg[0]*pi/180.0, a_deg[-1]*pi/180.0))
    plunger_pos_m = np.interp(pump_angle_rad, a_deg*pi/180.0, s_mm*1e-3)
    plunger_vel_ms = np.gradient(plunger_pos_m, dt)
    q_plunger = hyd.plunger_area_m2 * plunger_vel_ms

    results = {k: np.zeros_like(time_s) for k in ["line_pressure_pa", "needle_lift_m", "mdot_fuel_kg_s"]}
    
    # Spring preload force from opening pressure
    f_preload_pilot = nozzle.pilot_open_bar * 1e5 * needle.seat_area_m2
    
    for i in range(n_steps - 1):
        deriv = np.zeros_like(state)
        p_injector, x_needle, v_needle = state[-4], state[-2], state[-1]
        
        # Needle dynamics
        f_pressure = p_injector * needle.seat_area_m2
        f_spring = f_preload_pilot + needle.spring_k_n_per_m * x_needle
        f_damping = needle.damping_coeff_ns_per_m * v_needle
        f_net = f_pressure - f_spring - f_damping
        
        a_needle = f_net / needle.mass_kg if x_needle >= 0 else 0
        v_new = v_needle + a_needle * dt
        x_new = x_needle + v_new * dt
        
        if x_new < 0: x_new, v_new = 0, 0 # Needle hits seat
        if x_new > needle.max_lift_m: x_new, v_new = needle.max_lift_m, 0 # Needle hits stop

        deriv[-2], deriv[-1] = v_new - v_needle, a_needle
        
        # Nozzle flow
        area_eff = nozzle.area_m2 * nozzle.discharge_coeff * (x_new / needle.max_lift_m)
        dp_nozzle = max(0.0, p_injector - p_back)
        m_dot_noz = area_eff * sqrt(2.0 * rho * dp_nozzle)
        q_nozzle = m_dot_noz / rho
        
        results["mdot_fuel_kg_s"][i] = m_dot_noz
        results["line_pressure_pa"][i] = p_injector
        results["needle_lift_m"][i] = x_new

        # Line dynamics (mass and momentum)
        for j in range(N):
            p_idx, q_idx = 2*j, 2*j+1
            q_in = q_plunger[i] if j == 0 else state[q_idx-2]
            q_out = q_nozzle if j == N - 1 else state[q_idx]
            deriv[p_idx] = (K / V_seg) * (q_in - q_out)
            
            if j < N - 1:
                p_in, p_out = state[p_idx], state[p_idx+2]
                deriv[q_idx] = (A_line / (rho * L_seg)) * (p_in - p_out)

        state += deriv * dt
        state[-2], state[-1] = x_new, v_new # Update needle state separately
        state[::2] = np.maximum(p_back, state[::2])

    results["line_pressure_pa"][-1] = state[-4]
    results["needle_lift_m"][-1] = state[-2]
    
    return InjectionResult(time_s, results["line_pressure_pa"], results["needle_lift_m"], results["mdot_fuel_kg_s"])

