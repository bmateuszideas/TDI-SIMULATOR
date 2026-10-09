from __future__ import annotations

import numpy as np

# numpy 2.0 renamed trapz -> trapezoid. The repo pins numpy==1.26.4 in
# requirements.txt (trapz) while pyproject allows numpy>=1.26 (either name).
# Import `trapezoid` from this module instead of using np.trapezoid/np.trapz
# directly, so results are identical across supported numpy versions.
trapezoid = getattr(np, "trapezoid", None) or (np.trapezoid if hasattr(np, "trapezoid") else np.trapz)

__all__ = ["trapezoid"]
