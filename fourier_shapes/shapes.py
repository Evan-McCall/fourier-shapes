"""Built-in parametric shapes plus a unified signal provider."""
import numpy as np

from .signals import resample, normalize_signal
from .geo import get_geo_contour


def make_circle(n):
    return np.exp(2j * np.pi * np.linspace(0, 1, n, endpoint=False))


def make_square(n):
    t = np.linspace(0, 1, n, endpoint=False)
    pts = []
    for ti in t:
        s = ti * 4
        if s < 1:
            pts.append((-1 + 2*s) + 1j * (-1))
        elif s < 2:
            pts.append(1 + 1j * (-1 + 2*(s-1)))
        elif s < 3:
            pts.append((1 - 2*(s-2)) + 1j * 1)
        else:
            pts.append(-1 + 1j * (1 - 2*(s-3)))
    return np.array(pts)


def make_triangle(n):
    verts = [(-1-1j), (1-1j), (0+1j), (-1-1j)]
    pts = []
    segs = [(verts[i], verts[i+1]) for i in range(3)]
    per_seg = n // 3
    for a, b in segs:
        for k in range(per_seg):
            pts.append(a + (b - a) * k / per_seg)
    return resample(pts, n)


def make_star(n, points=5):
    angles = np.linspace(0, 2*np.pi, 2*points, endpoint=False)
    radii = [1 if i % 2 == 0 else 0.4 for i in range(2*points)]
    verts = [r * np.exp(1j * a) for r, a in zip(radii, angles)]
    return resample(verts, n)


def make_heart(n):
    t = np.linspace(0, 2*np.pi, n, endpoint=False)
    x = 16 * np.sin(t)**3
    y = 13*np.cos(t) - 5*np.cos(2*t) - 2*np.cos(3*t) - np.cos(4*t)
    return (x + 1j*y) / 16


def make_arrow(n):
    verts = [
        0+0j, 0.4+0j, 0.4-0.3j, 1+0j, 0.4+0.3j, 0.4+0j, 0.4+0.15j,
        -0.5+0.15j, -0.5-0.15j, 0.4-0.15j, 0.4+0j
    ]
    return resample(verts, n)


def make_spiral(n):
    t = np.linspace(0, 6*np.pi, n, endpoint=False)
    r = t / (6*np.pi)
    return r * np.exp(1j*t)


BUILTIN_SHAPES = {
    "circle": make_circle,
    "square": make_square,
    "triangle": make_triangle,
    "star": make_star,
    "heart": make_heart,
    "arrow": make_arrow,
    "spiral": make_spiral,
}


def get_shape_signal(name, n=512):
    """Return (complex signal, error message). One will be None."""
    key = name.lower().strip()

    if key in BUILTIN_SHAPES:
        sig = BUILTIN_SHAPES[key](n)
    else:
        coords = get_geo_contour(name)
        if coords is None:
            return None, f"Shape '{name}' not found."
        sig = resample(coords, n)

    return normalize_signal(np.array(sig)), None
