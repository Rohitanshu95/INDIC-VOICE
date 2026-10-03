"""Device and compute precision helper utilities."""

import os
from typing import Any, Tuple


def get_device(preference: str = "auto") -> str:
    """Determine the optimal compute device (cuda or cpu).

    Args:
        preference: 'auto', 'cuda', 'cpu', or explicit device string like 'cuda:0'.

    Returns:
        Device string ('cuda', 'cuda:0', or 'cpu').
    """
    pref = (preference or "auto").lower().strip()

    # Environment override
    env_override = os.getenv("INDICVOICE_DEVICE", "").strip().lower()
    if env_override:
        pref = env_override

    if pref == "cpu":
        return "cpu"

    if pref.startswith("cuda"):
        try:
            import torch

            if torch.cuda.is_available():
                return pref
            return "cpu"
        except ImportError:
            return "cpu"

    # auto
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
        return "cpu"
    except ImportError:
        return "cpu"


def get_torch_dtype(device: str) -> Any:
    """Return appropriate torch dtype for device (fp16 on CUDA, fp32 on CPU)."""
    try:
        import torch

        if "cuda" in device:
            # Use float16 on GPU to save VRAM while preserving audio quality
            return torch.float16
        return torch.float32
    except ImportError:
        return None


def get_device_and_dtype(preference: str = "auto") -> Tuple[str, Any]:
    """Return tuple of (device_str, torch_dtype)."""
    device = get_device(preference)
    dtype = get_torch_dtype(device)
    return device, dtype
