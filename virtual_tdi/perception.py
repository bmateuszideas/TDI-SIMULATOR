"""ECU sensor perception model (TODO.md Faza 2.C.1).

Real ECUs do not see the plant directly: signals are sampled, filtered,
delayed and noisy. This module wraps a physical signal into a perceived
signal with:

- first-order lag (sensor + filter time constant),
- transport/sample delay (whole samples of dt),
- optional bias and Gaussian noise (reproducible via numpy Generator).

Typical values for a 1990s ALH EDC:
- MAP sensor: tau ~ 5-20 ms, delay 1 sample (10 ms).
- EGT (thermocouple): tau ~ 0.5-1.5 s (dominant lag, e.g. slowdown relay).
- RPM: measured from crank wheel over ~0.25 rev; tau ~ 10-30 ms.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SensorConfig:
    name: str
    tau_s: float = 0.05          # first-order lag time constant
    delay_s: float = 0.0         # transport/sample delay
    bias: float = 0.0            # constant offset (e.g. sensor calibration)
    noise_std: float = 0.0       # Gaussian noise sigma (same units as signal)
    init_value: float | None = None


class SensorModel:
    """First-order lag + delay + bias/noise perception of one signal."""

    def __init__(self, config: SensorConfig, *, dt_s: float,
                 seed: int | None = None):
        self.cfg = config
        self.dt_s = float(dt_s)
        self._rng = np.random.default_rng(seed)
        self._state = (float(config.init_value) if config.init_value is not None
                       else 0.0)
        self._delay_buffer: list[float] = []
        n_delay = int(round(config.delay_s / max(1e-9, self.dt_s)))
        self._delay_n = max(0, n_delay)

    def step(self, true_value: float) -> float:
        """Advance the perception by one dt; returns the perceived value."""
        tau = max(1e-9, self.cfg.tau_s)
        alpha = self.dt_s / (tau + self.dt_s)
        self._state += alpha * (float(true_value) - self._state)
        # push the lagged state through the delay line
        self._delay_buffer.append(self._state)
        if len(self._delay_buffer) > self._delay_n:
            perceived = self._delay_buffer.pop(0)
        else:
            perceived = self._delay_buffer[0]
        if self.cfg.noise_std > 0.0:
            perceived = perceived + self._rng.normal(0.0, self.cfg.noise_std)
        return float(perceived + self.cfg.bias)

    @property
    def state(self) -> float:
        return self._state


@dataclass(frozen=True)
class PerceptionConfig:
    """Perception layer for the sensors used by the transient governor."""
    rpm: SensorConfig = SensorConfig(name="rpm", tau_s=0.02, delay_s=0.02,
                                     noise_std=2.0)          # rpm
    map_kpa: SensorConfig = SensorConfig(name="map", tau_s=0.01, delay_s=0.01,
                                         noise_std=1.5)       # kPa
    egt_k: SensorConfig = SensorConfig(name="egt", tau_s=1.0, delay_s=0.1,
                                       noise_std=5.0)          # K
    enabled: bool = False


class PerceptionLayer:
    """Wraps a PerceptionConfig into live SensorModel instances."""

    def __init__(self, config: PerceptionConfig, *, dt_s: float, seed: int = 0):
        self.cfg = config
        self.rpm = SensorModel(config.rpm, dt_s=dt_s, seed=seed)
        self.map_kpa = SensorModel(config.map_kpa, dt_s=dt_s, seed=seed + 1)
        self.egt_k = SensorModel(config.egt_k, dt_s=dt_s, seed=seed + 2)

    def perceive(self, *, rpm: float, map_kpa: float, egt_k: float):
        return (self.rpm.step(rpm), self.map_kpa.step(map_kpa),
                self.egt_k.step(egt_k))
