"""Resampling and normalization for complex-valued path signals."""
import numpy as np


def resample(points, n):
    """Resample a closed polygon to exactly n evenly-spaced points.
    Accepts either Nx2 real arrays or 1D complex arrays."""
    pts = np.array(points)
    if np.iscomplexobj(pts):
        pts = np.stack([pts.real, pts.imag], axis=1)
    diffs = np.diff(pts, axis=0, prepend=pts[[-1]])
    dist = np.sqrt((diffs**2).sum(axis=1))
    cumlen = np.cumsum(dist)
    total = cumlen[-1]
    target = np.linspace(0, total, n, endpoint=False)
    xi = np.interp(target, cumlen, pts[:, 0])
    yi = np.interp(target, cumlen, pts[:, 1])
    return xi + 1j * yi


def normalize_signal(signal):
    """Center and scale signal to fit in [-1, 1]."""
    real, imag = signal.real, signal.imag
    cx = (real.max() + real.min()) / 2
    cy = (imag.max() + imag.min()) / 2
    signal = signal - (cx + 1j * cy)
    scale = max(signal.real.max() - signal.real.min(),
                signal.imag.max() - signal.imag.min()) / 2
    if scale > 0:
        signal /= scale
    return signal
