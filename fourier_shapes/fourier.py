"""DFT decomposition and epicycle evaluation."""
import numpy as np


def compute_dft(signal):
    """Compute DFT and return epicycles as (freq, amplitude, phase),
    sorted by amplitude descending."""
    N = len(signal)
    X = np.fft.fft(signal) / N
    freqs = np.fft.fftfreq(N, d=1.0/N)
    order = np.argsort(-np.abs(X))
    return [(freqs[i], np.abs(X[i]), np.angle(X[i])) for i in order]


def epicycles_point(epicycles, t, n_circles):
    """Compute tip position and all circle centers for time t in [0, 1]."""
    centers = [0+0j]
    x = 0+0j
    for freq, amp, phase in epicycles[:n_circles]:
        x += amp * np.exp(1j * (2 * np.pi * freq * t + phase))
        centers.append(x)
    return x, centers


def build_equation_str(epicycles, n_terms=6):
    """Build a human-readable Fourier series string showing the top terms."""
    parts = []
    for freq, amp, phase in epicycles[:n_terms]:
        if amp < 1e-6:
            continue
        parts.append(
            f"{amp:.3f}·e^(i(2π·{int(round(freq))}·t{phase:+.3f}))"
        )
    eq = "f(t) = " + "\n      + ".join(parts)
    if len(epicycles) > n_terms:
        eq += f"\n      + ... ({len(epicycles) - n_terms} more terms)"
    return eq
