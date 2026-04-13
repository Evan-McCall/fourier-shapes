"""Matplotlib-based interactive app for drawing shapes with epicycles."""
import sys

import numpy as np
import matplotlib
if sys.platform == "darwin":
    matplotlib.use("macosx")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import TextBox, Button, Slider

from .shapes import get_shape_signal
from .fourier import compute_dft, epicycles_point, build_equation_str


BG = "#0d0d1a"
PANEL_BG = "#1a1a33"
SPINE = "#333355"
TEXT = "#aaaacc"
MUTED = "#888899"
GRID = "#1a1a33"
TRACE = "#00ffcc"
TARGET = "#334455"
TIP = "#ff6688"
CIRCLE = "#334466"
ARM = "#5566aa"
EQ = "#88eebb"
BTN = "#223366"
BTN_HOVER = "#3344aa"


class FourierApp:
    N_SAMPLES = 512
    N_CIRCLES = 50
    INTERVAL_MS = 20

    def __init__(self):
        self.epicycles = []
        self.trace = []
        self.target_path = []
        self.anim = None
        self.shape_name = ""
        self.circles_artists = []
        self.lines_artists = []

        self._build_ui()

    def _build_ui(self):
        self.fig = plt.figure(figsize=(14, 8), facecolor=BG)
        self.fig.canvas.manager.set_window_title("Fourier Shape Generator")

        self.ax = self.fig.add_axes([0.03, 0.15, 0.60, 0.80])
        self.ax_eq = self.fig.add_axes([0.65, 0.15, 0.33, 0.80])

        for ax in [self.ax, self.ax_eq]:
            ax.set_facecolor(BG)
            for spine in ax.spines.values():
                spine.set_color(SPINE)

        self.ax.set_xlim(-1.5, 1.5)
        self.ax.set_ylim(-1.5, 1.5)
        self.ax.set_aspect("equal")
        self.ax.tick_params(colors="#555577")
        self.ax.grid(True, color=GRID, linewidth=0.5)
        self.ax.set_title("Fourier Epicycles", color=TEXT, fontsize=13)

        self.ax_eq.set_xlim(0, 1)
        self.ax_eq.set_ylim(0, 1)
        self.ax_eq.axis("off")
        self.ax_eq.set_title("Fourier Series Equation", color=TEXT, fontsize=11)
        self.eq_text = self.ax_eq.text(
            0.05, 0.92, "", transform=self.ax_eq.transAxes,
            color=EQ, fontsize=8.5, va="top", family="monospace", wrap=True
        )
        self.info_text = self.ax_eq.text(
            0.05, 0.08, "", transform=self.ax_eq.transAxes,
            color=TEXT, fontsize=8, va="bottom", family="monospace"
        )

        self.trace_line, = self.ax.plot([], [], color=TRACE, lw=1.2, alpha=0.85)
        self.target_line, = self.ax.plot([], [], color=TARGET, lw=1.0,
                                         linestyle="--", alpha=0.5)
        self.tip_dot, = self.ax.plot([], [], "o", color=TIP, ms=5)

        self._build_widgets()
        plt.rcParams["axes.facecolor"] = BG

    def _build_widgets(self):
        ax_box = self.fig.add_axes([0.03, 0.04, 0.42, 0.06])
        ax_btn = self.fig.add_axes([0.47, 0.04, 0.12, 0.06])
        ax_sld_lbl = self.fig.add_axes([0.65, 0.06, 0.05, 0.03])
        ax_sld = self.fig.add_axes([0.70, 0.04, 0.27, 0.04])

        ax_box.set_facecolor(PANEL_BG)
        ax_btn.set_facecolor(PANEL_BG)
        ax_sld.set_facecolor(PANEL_BG)
        ax_sld_lbl.axis("off")
        ax_sld_lbl.text(0.5, 0.5, "Circles:", color=TEXT,
                        ha="center", va="center", fontsize=9)

        self.textbox = TextBox(
            ax_box, "Shape: ", initial="United States of America",
            color=PANEL_BG, hovercolor="#222244", label_pad=0.02,
        )
        self.textbox.label.set_color(TEXT)
        self.textbox.text_disp.set_color("#ffffff")

        self.btn = Button(ax_btn, "Generate", color=BTN, hovercolor=BTN_HOVER)
        self.btn.label.set_color("#ffffff")
        self.btn.on_clicked(self._on_generate)
        self.textbox.on_submit(self._on_generate)

        self.slider = Slider(ax_sld, "", 1, 200, valinit=self.N_CIRCLES,
                             valstep=1, color="#334488")
        self.slider.label.set_color(TEXT)
        self.slider.valtext.set_color(TEXT)
        self.slider.on_changed(self._on_slider)

        self.status_text = self.fig.text(
            0.03, 0.01, "Enter a shape name and press Generate or hit Enter.",
            color=MUTED, fontsize=8,
        )

    def _on_slider(self, val):
        self.N_CIRCLES = int(val)

    def _rebuild_circle_artists(self, n):
        for art in self.circles_artists + self.lines_artists:
            art.remove()
        self.circles_artists.clear()
        self.lines_artists.clear()
        for _ in range(n):
            circ = plt.Circle((0, 0), 0, fill=False, color=CIRCLE,
                              lw=0.6, alpha=0.5)
            self.ax.add_patch(circ)
            self.circles_artists.append(circ)
            ln, = self.ax.plot([], [], color=ARM, lw=0.8, alpha=0.7)
            self.lines_artists.append(ln)

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
        self.target_path = sig

        self._update_info_panel(name)

        closed = np.append(self.target_path, self.target_path[0])
        self.target_line.set_data(closed.real, closed.imag)

        self.trace = []
        n = min(self.N_CIRCLES, len(self.epicycles))
        self._rebuild_circle_artists(n)

        if self.anim is not None:
            self.anim.event_source.stop()

        self.status_text.set_text(
            f"Drawing '{name}' with {self.N_CIRCLES} circles — "
            f"{len(self.epicycles)} Fourier terms total."
        )
        self.anim = FuncAnimation(
            self.fig, self._update,
            frames=self.N_SAMPLES,
            interval=self.INTERVAL_MS,
            blit=False, repeat=True,
        )
        self.fig.canvas.draw_idle()

    def _update_info_panel(self, name):
        self.eq_text.set_text(build_equation_str(self.epicycles, n_terms=8))
        sig_amps = [amp for _, amp, _ in self.epicycles]
        total_amp = sum(sig_amps)
        captured = (sum(sig_amps[:self.N_CIRCLES]) / total_amp * 100
                    if total_amp else 0)
        self.info_text.set_text(
            f"Shape: {name}\n"
            f"Total DFT terms: {len(self.epicycles)}\n"
            f"Circles shown: {self.N_CIRCLES}\n"
            f"Energy captured: {captured:.1f}%\n\n"
            f"Drag slider to add/remove circles."
        )

    def _update(self, frame):
        if frame == 0:
            self.trace.clear()

        t = frame / self.N_SAMPLES
        n = min(int(self.slider.val), len(self.epicycles))

        tip, centers = epicycles_point(self.epicycles, t, n)
        self.trace.append(tip)

        if len(self.circles_artists) != n:
            self._rebuild_circle_artists(n)

        for i, (circ, ln) in enumerate(zip(self.circles_artists, self.lines_artists)):
            cx, cy = centers[i].real, centers[i].imag
            circ.center = (cx, cy)
            circ.radius = self.epicycles[i][1]
            nx, ny = centers[i+1].real, centers[i+1].imag
            ln.set_data([cx, nx], [cy, ny])

        tx = [p.real for p in self.trace]
        ty = [p.imag for p in self.trace]
        self.trace_line.set_data(tx, ty)
        self.tip_dot.set_data([tip.real], [tip.imag])

        self._autoscale(tx, ty, centers)
        return []

    def _autoscale(self, tx, ty, centers):
        all_x = tx + [c.real for c in centers]
        all_y = ty + [c.imag for c in centers]
        if not all_x or not all_y:
            return
        pad = 0.2
        xmin, xmax = min(all_x) - pad, max(all_x) + pad
        ymin, ymax = min(all_y) - pad, max(all_y) + pad
        span = max(xmax - xmin, ymax - ymin) / 2
        mx, my = (xmin + xmax) / 2, (ymin + ymax) / 2
        self.ax.set_xlim(mx - span, mx + span)
        self.ax.set_ylim(my - span, my + span)

    def run(self):
        self._start_animation("United States of America")
        plt.show()
