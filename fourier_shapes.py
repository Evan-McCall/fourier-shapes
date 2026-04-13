"""
Fourier Shape Generator
Prompt a shape name and watch it be drawn by rotating circles (epicycles).
"""

import sys
import numpy as np
import matplotlib
if sys.platform == "darwin":
    matplotlib.use("macosx")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import TextBox, Button
import geopandas as gpd
import warnings
warnings.filterwarnings("ignore")

# ─── Shape Providers ──────────────────────────────────────────────────────────

def resample(points, n):
    """Resample a closed polygon to exactly n evenly-spaced points.
    Accepts either Nx2 real arrays or 1D complex arrays."""
    pts = np.array(points)
    if np.iscomplexobj(pts):
        # Convert complex to Nx2
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


GEO_SHAPES = {
    "united states": "United States of America",
    "usa": "United States of America",
    "united states of america": "United States of America",
    "china": "China",
    "russia": "Russia",
    "brazil": "Brazil",
    "australia": "Australia",
    "india": "India",
    "canada": "Canada",
    "france": "France",
    "germany": "Germany",
    "japan": "Japan",
    "italy": "Italy",
    "spain": "Spain",
    "mexico": "Mexico",
    "uk": "United Kingdom",
    "united kingdom": "United Kingdom",
    "south africa": "South Africa",
    "argentina": "Argentina",
    "egypt": "Egypt",
    "turkey": "Turkey",
    "nigeria": "Nigeria",
    "indonesia": "Indonesia",
    "thailand": "Thailand",
    "sweden": "Sweden",
    "norway": "Norway",
    "poland": "Poland",
    "ukraine": "Ukraine",
    "iraq": "Iraq",
    "iran": "Iran",
    "saudi arabia": "Saudi Arabia",
    "colombia": "Colombia",
    "peru": "Peru",
    "venezuela": "Venezuela",
    "chile": "Chile",
    "kazakhstan": "Kazakhstan",
    "mongolia": "Mongolia",
    "south korea": "South Korea",
    "north korea": "North Korea",
    "vietnam": "Vietnam",
    "malaysia": "Malaysia",
    "philippines": "Philippines",
    "pakistan": "Pakistan",
    "afghanistan": "Afghanistan",
    "algeria": "Algeria",
    "angola": "Angola",
    "mali": "Mali",
    "ethiopia": "Ethiopia",
    "mozambique": "Mozambique",
    "madagascar": "Madagascar",
    "new zealand": "New Zealand",
    "bolivia": "Bolivia",
    "paraguay": "Paraguay",
    "uruguay": "Uruguay",
    "cuba": "Cuba",
    "portugal": "Portugal",
    "greece": "Greece",
    "romania": "Romania",
    "finland": "Finland",
    "denmark": "Denmark",
}


_world_data = None

def get_world_data():
    global _world_data
    if _world_data is None:
        import geopandas as gpd
        import os, urllib.request, zipfile, tempfile

        # Cache path
        cache_dir = os.path.expanduser("~/.cache/fourier_shapes")
        os.makedirs(cache_dir, exist_ok=True)
        shp_path = os.path.join(cache_dir, "ne_110m_admin_0_countries.shp")

        if not os.path.exists(shp_path):
            url = ("https://naciscdn.org/naturalearth/110m/cultural/"
                   "ne_110m_admin_0_countries.zip")
            zip_path = os.path.join(cache_dir, "countries.zip")
            print(f"Downloading country data (one-time)...")
            urllib.request.urlretrieve(url, zip_path)
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(cache_dir)
            os.remove(zip_path)

        _world_data = gpd.read_file(shp_path)
    return _world_data


def get_geo_contour(name):
    """Get the largest polygon contour for a country by name."""
    world = get_world_data()
    key = name.lower().strip()
    canonical = GEO_SHAPES.get(key)

    # Search across NAME, NAME_LONG, ADMIN columns
    name_cols = [c for c in ["NAME", "NAME_LONG", "ADMIN", "SOVEREIGNT"] if c in world.columns]

    row = None
    if canonical:
        for col in name_cols:
            matches = world[world[col].str.lower() == canonical.lower()]
            if len(matches):
                row = matches.iloc[0]
                break
    if row is None:
        # fuzzy substring match
        for col in name_cols:
            matches = world[world[col].str.lower().str.contains(key, na=False)]
            if len(matches):
                row = matches.iloc[0]
                break
    if row is None:
        return None

    geom = row.geometry
    # Handle MultiPolygon — pick largest
    from shapely.geometry import MultiPolygon, Polygon
    if isinstance(geom, MultiPolygon):
        geom = max(geom.geoms, key=lambda g: g.area)

    coords = np.array(geom.exterior.coords)
    return coords


BUILTIN_SHAPES = {
    "circle": lambda n: np.exp(2j * np.pi * np.linspace(0, 1, n, endpoint=False)),
    "square": None,
    "triangle": None,
    "star": None,
    "heart": None,
    "arrow": None,
    "spiral": None,
}


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
    return r * np.exp(1j*t) / 1.0


def get_shape_signal(name, n=512):
    """Return complex signal for a given shape name."""
    key = name.lower().strip()

    # Try built-in shapes first
    if key == "circle":
        sig = BUILTIN_SHAPES["circle"](n)
    elif key == "square":
        sig = make_square(n)
    elif key == "triangle":
        sig = make_triangle(n)
    elif key == "star":
        sig = make_star(n)
    elif key == "heart":
        sig = make_heart(n)
    elif key == "arrow":
        sig = make_arrow(n)
    elif key == "spiral":
        sig = make_spiral(n)
    else:
        # Try geographic shape
        coords = get_geo_contour(name)
        if coords is None:
            return None, f"Shape '{name}' not found."
        sig = resample(coords, n)

    sig = normalize_signal(np.array(sig))
    return sig, None


# ─── Fourier Engine ───────────────────────────────────────────────────────────

def compute_dft(signal):
    """Compute DFT and return sorted epicycles as (freq, amplitude, phase)."""
    N = len(signal)
    X = np.fft.fft(signal) / N
    freqs = np.fft.fftfreq(N, d=1.0/N)
    # Sort by amplitude descending
    order = np.argsort(-np.abs(X))
    epicycles = []
    for i in order:
        amp = np.abs(X[i])
        phase = np.angle(X[i])
        freq = freqs[i]
        epicycles.append((freq, amp, phase))
    return epicycles


def epicycles_point(epicycles, t, n_circles):
    """Compute tip position and all circle centers for time t (0..1)."""
    centers = [0+0j]
    x = 0+0j
    for freq, amp, phase in epicycles[:n_circles]:
        x += amp * np.exp(1j * (2 * np.pi * freq * t + phase))
        centers.append(x)
    return x, centers


# ─── Equation Formatter ───────────────────────────────────────────────────────

def build_equation_str(epicycles, n_terms=6):
    """Build a human-readable Fourier series string."""
    parts = []
    for i, (freq, amp, phase) in enumerate(epicycles[:n_terms]):
        if amp < 1e-6:
            continue
        a_str = f"{amp:.3f}"
        p_str = f"{phase:+.3f}"
        f_str = f"{int(round(freq))}"
        parts.append(f"{a_str}·e^(i(2π·{f_str}·t{p_str}))")
    eq = "f(t) = " + "\n      + ".join(parts)
    if len(epicycles) > n_terms:
        eq += f"\n      + ... ({len(epicycles) - n_terms} more terms)"
    return eq


# ─── App ──────────────────────────────────────────────────────────────────────

class FourierApp:
    N_SAMPLES = 512
    N_CIRCLES = 50   # circles used for drawing
    INTERVAL_MS = 20

    def __init__(self):
        self.epicycles = []
        self.trace = []
        self.target_path = []
        self.frame = 0
        self.total_frames = 300
        self.anim = None
        self.running = False
        self.shape_name = ""

        self._build_ui()

    def _build_ui(self):
        self.fig = plt.figure(figsize=(14, 8), facecolor="#0d0d1a")
        self.fig.canvas.manager.set_window_title("Fourier Shape Generator")

        # Layout: main axes left, equation text right
        self.ax = self.fig.add_axes([0.03, 0.15, 0.60, 0.80])
        self.ax_eq = self.fig.add_axes([0.65, 0.15, 0.33, 0.80])

        for ax in [self.ax, self.ax_eq]:
            ax.set_facecolor("#0d0d1a")
            for spine in ax.spines.values():
                spine.set_color("#333355")

        self.ax.set_xlim(-1.5, 1.5)
        self.ax.set_ylim(-1.5, 1.5)
        self.ax.set_aspect("equal")
        self.ax.tick_params(colors="#555577")
        self.ax.grid(True, color="#1a1a33", linewidth=0.5)
        self.ax.set_title("Fourier Epicycles", color="#aaaacc", fontsize=13)

        self.ax_eq.set_xlim(0, 1)
        self.ax_eq.set_ylim(0, 1)
        self.ax_eq.axis("off")
        self.ax_eq.set_title("Fourier Series Equation", color="#aaaacc", fontsize=11)
        self.eq_text = self.ax_eq.text(
            0.05, 0.92, "", transform=self.ax_eq.transAxes,
            color="#88eebb", fontsize=8.5, va="top", family="monospace",
            wrap=True
        )
        self.info_text = self.ax_eq.text(
            0.05, 0.08, "", transform=self.ax_eq.transAxes,
            color="#aaaacc", fontsize=8, va="bottom", family="monospace"
        )

        # Drawing elements
        self.circles_artists = []
        self.lines_artists = []
        self.trace_line, = self.ax.plot([], [], color="#00ffcc", lw=1.2, alpha=0.85)
        self.target_line, = self.ax.plot([], [], color="#334455", lw=1.0,
                                          linestyle="--", alpha=0.5)
        self.tip_dot, = self.ax.plot([], [], "o", color="#ff6688", ms=5)

        # Widgets
        ax_box = self.fig.add_axes([0.03, 0.04, 0.42, 0.06])
        ax_btn = self.fig.add_axes([0.47, 0.04, 0.12, 0.06])
        ax_sld_lbl = self.fig.add_axes([0.65, 0.06, 0.05, 0.03])
        ax_sld = self.fig.add_axes([0.70, 0.04, 0.27, 0.04])

        ax_box.set_facecolor("#1a1a33")
        ax_btn.set_facecolor("#1a1a33")
        ax_sld.set_facecolor("#1a1a33")
        ax_sld_lbl.axis("off")
        ax_sld_lbl.text(0.5, 0.5, "Circles:", color="#aaaacc",
                        ha="center", va="center", fontsize=9)

        self.textbox = TextBox(ax_box, "Shape: ", initial="United States of America",
                               color="#1a1a33", hovercolor="#222244",
                               label_pad=0.02)
        self.textbox.label.set_color("#aaaacc")
        self.textbox.text_disp.set_color("#ffffff")

        self.btn = Button(ax_btn, "Generate", color="#223366", hovercolor="#3344aa")
        self.btn.label.set_color("#ffffff")
        self.btn.on_clicked(self._on_generate)
        self.textbox.on_submit(self._on_generate)

        from matplotlib.widgets import Slider
        self.slider = Slider(ax_sld, "", 1, 200, valinit=self.N_CIRCLES,
                             valstep=1, color="#334488")
        self.slider.label.set_color("#aaaacc")
        self.slider.valtext.set_color("#aaaacc")
        self.slider.on_changed(self._on_slider)

        self.status_text = self.fig.text(
            0.03, 0.01, "Enter a shape name and press Generate or hit Enter.",
            color="#888899", fontsize=8
        )

        plt.rcParams["axes.facecolor"] = "#0d0d1a"

    def _on_slider(self, val):
        self.N_CIRCLES = int(val)

    def _on_generate(self, event=None):
        name = self.textbox.text.strip()
        if not name:
            return
        self._start_animation(name)

    def _start_animation(self, name):
        self.status_text.set_text(f"Loading '{name}'...")
        self.fig.canvas.draw_idle()

        sig, err = get_shape_signal(name, self.N_SAMPLES)
        if err:
            self.status_text.set_text(f"Error: {err}")
            self.fig.canvas.draw_idle()
            return

        self.shape_name = name
        self.epicycles = compute_dft(sig)
        self.target_path = [
            epicycles_point(self.epicycles, k / self.N_SAMPLES, len(self.epicycles))[0]
            for k in range(self.N_SAMPLES)
        ]

        # Update equation
        eq_str = build_equation_str(self.epicycles, n_terms=8)
        self.eq_text.set_text(eq_str)
        sig_amps = [amp for _, amp, _ in self.epicycles]
        total_amp = sum(sig_amps)
        captured = sum(sig_amps[:self.N_CIRCLES]) / total_amp * 100 if total_amp else 0
        self.info_text.set_text(
            f"Shape: {name}\n"
            f"Total DFT terms: {len(self.epicycles)}\n"
            f"Circles shown: {self.N_CIRCLES}\n"
            f"Energy captured: {captured:.1f}%\n\n"
            f"Drag slider to add/remove circles."
        )

        # Draw target shape faintly
        tx = [p.real for p in self.target_path] + [self.target_path[0].real]
        ty = [p.imag for p in self.target_path] + [self.target_path[0].imag]
        self.target_line.set_data(tx, ty)

        # Reset trace
        self.trace = []
        self.frame = 0

        # Clear old circle artists
        for art in self.circles_artists + self.lines_artists:
            art.remove()
        self.circles_artists.clear()
        self.lines_artists.clear()

        n = min(self.N_CIRCLES, len(self.epicycles))
        for _ in range(n):
            circ = plt.Circle((0, 0), 0, fill=False, color="#334466",
                               lw=0.6, alpha=0.5)
            self.ax.add_patch(circ)
            self.circles_artists.append(circ)
            ln, = self.ax.plot([], [], color="#5566aa", lw=0.8, alpha=0.7)
            self.lines_artists.append(ln)

        if self.anim is not None:
            self.anim.event_source.stop()

        self.total_frames = self.N_SAMPLES
        self.status_text.set_text(
            f"Drawing '{name}' with {self.N_CIRCLES} circles — "
            f"{len(self.epicycles)} Fourier terms total."
        )
        self.anim = FuncAnimation(
            self.fig, self._update,
            frames=self.total_frames,
            interval=self.INTERVAL_MS,
            blit=False, repeat=True
        )
        self.fig.canvas.draw_idle()

    def _update(self, frame):
        t = frame / self.N_SAMPLES
        n = min(self.N_CIRCLES, len(self.epicycles))

        # Recheck slider
        n = min(int(self.slider.val), len(self.epicycles))

        tip, centers = epicycles_point(self.epicycles, t, n)
        self.trace.append(tip)

        # Rebuild circle artists if count changed
        if len(self.circles_artists) != n:
            for art in self.circles_artists + self.lines_artists:
                art.remove()
            self.circles_artists.clear()
            self.lines_artists.clear()
            for _ in range(n):
                circ = plt.Circle((0, 0), 0, fill=False, color="#334466",
                                   lw=0.6, alpha=0.5)
                self.ax.add_patch(circ)
                self.circles_artists.append(circ)
                ln, = self.ax.plot([], [], color="#5566aa", lw=0.8, alpha=0.7)
                self.lines_artists.append(ln)

        # Update circles and arms
        for i, (circ, ln) in enumerate(zip(self.circles_artists, self.lines_artists)):
            cx, cy = centers[i].real, centers[i].imag
            r = self.epicycles[i][1]
            circ.center = (cx, cy)
            circ.radius = r
            nx, ny = centers[i+1].real, centers[i+1].imag
            ln.set_data([cx, nx], [cy, ny])

        # Trace
        tx = [p.real for p in self.trace]
        ty = [p.imag for p in self.trace]
        self.trace_line.set_data(tx, ty)
        self.tip_dot.set_data([tip.real], [tip.imag])

        # Dynamic axis limits
        all_x = tx + [c.real for c in centers]
        all_y = ty + [c.imag for c in centers]
        if all_x and all_y:
            pad = 0.2
            xmin, xmax = min(all_x) - pad, max(all_x) + pad
            ymin, ymax = min(all_y) - pad, max(all_y) + pad
            span = max(xmax - xmin, ymax - ymin) / 2
            mx, my = (xmin + xmax) / 2, (ymin + ymax) / 2
            self.ax.set_xlim(mx - span, mx + span)
            self.ax.set_ylim(my - span, my + span)

        # If loop restarted, clear trace
        if frame == 0:
            self.trace.clear()

        return []

    def run(self):
        # Auto-load default shape
        self._start_animation("United States of America")
        plt.show()


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = FourierApp()
    app.run()
