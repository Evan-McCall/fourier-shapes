<div align="center">

# 🌀 Fourier Shapes

**Watch any shape emerge from a chorus of rotating circles — the Fourier series, made visible.**

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/Evan-McCall/fourier-shapes?style=social)](https://github.com/Evan-McCall/fourier-shapes/stargazers)
[![Last Commit](https://img.shields.io/github/last-commit/Evan-McCall/fourier-shapes)](https://github.com/Evan-McCall/fourier-shapes/commits/main)

</div>

Type `heart`, `spiral`, or `Japan` into an interactive matplotlib app and watch a chain of rotating circles — one per Fourier term — reconstruct the outline in real time. Drag a slider to control how many circles participate, and see how quickly the approximation sharpens as you add higher-frequency terms.

It's a small, fast, honest hobby project for anyone who wants to *see* what a Fourier series actually does.

---

## ⚡ Quick Start

```bash
git clone https://github.com/Evan-McCall/fourier-shapes.git
cd fourier-shapes
pip install -r requirements.txt
python -m fourier_shapes
```

That's it. Type a shape name, hit **Enter**, and watch it draw itself.

---

## 📑 Table of Contents

- [Features](#-features)
- [Installation](#-installation)
- [Usage](#-usage)
- [How It Works](#-how-it-works)
- [Project Layout](#-project-layout)
- [Supported Shapes](#-supported-shapes)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

- **Interactive matplotlib UI** — type a shape, press Generate, watch it draw itself
- **7 built-in shapes** — circle, square, triangle, star, heart, arrow, spiral
- **~60 country outlines** loaded on demand from Natural Earth's 1:110m admin boundaries
- **Live circle-count slider** (1–200) — see how higher-frequency terms sharpen the approximation
- **Energy readout** showing the percentage of signal captured by your chosen number of circles
- **Live Fourier series equation panel** with the top terms, updated per shape
- **Dark theme** out of the box
- **Zero config** — one command, no flags, no setup file
- **Cross-platform** — macOS uses the native `macosx` backend; Linux/Windows fall back to the default

---

## 📦 Installation

### Requirements

- **Python** 3.10 or newer
- A GUI-capable matplotlib backend:
  - **macOS** — works out of the box (uses `macosx`)
  - **Linux** — `TkAgg` (ships with `python3-tk`) or `Qt5Agg`
  - **Windows** — `TkAgg` (default)

### From source

```bash
git clone https://github.com/Evan-McCall/fourier-shapes.git
cd fourier-shapes

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

> **Note:** `geopandas` pulls in `shapely`, `pyproj`, and `fiona`, which can take a minute to install.

### Dependencies

| Package      | Purpose                                      |
| ------------ | -------------------------------------------- |
| `numpy`      | FFT and vector math                          |
| `matplotlib` | UI, animation, plotting                      |
| `geopandas`  | Reading Natural Earth shapefiles             |
| `shapely`    | Polygon operations (largest-region selection)|

---

## 🎮 Usage

Launch the app:

```bash
python -m fourier_shapes
```

Then:

1. Type a **shape name** in the text box — e.g. `heart`, `spiral`, `Japan`, `Brazil`
2. Press **Enter** or click **Generate**
3. Drag the **Circles** slider (1–200) to change how many Fourier terms are drawn
4. Watch the equation panel and energy readout update as you change shapes

The first time you request a country, the app downloads ~1 MB of Natural Earth data into `~/.cache/fourier_shapes/`. Subsequent runs are offline.

---

## 🧠 How It Works

Any closed 2D path can be written as a sum of rotating complex exponentials — a Fourier series. The app does four things:

1. **Samples** a shape's outline into an `N`-point complex-valued signal `f(t)` on `t ∈ [0, 1)`
2. **Decomposes** it via `numpy.fft.fft`, yielding one complex coefficient per integer frequency
3. **Sorts** the terms by amplitude, so the biggest contributors come first
4. **Animates** each term as a rotating circle, each attached to the tip of the previous one — the tip of the last circle traces the reconstructed path

The series being visualized:

```
          ∞
f(t)  =   Σ   c_k · exp(i · 2π · k · t)
         k=-∞

where   c_k = a_k · exp(i · φ_k)
```

Each `c_k` becomes one circle: **radius** `a_k`, **angular velocity** `k`, **starting phase** `φ_k`. Truncating the sum at `N` terms gives you the slider: fewer circles means a blurrier reconstruction, more circles means more detail.

---

## 🗂️ Project Layout

```
fourier_shapes/
├── __init__.py    # Package exports
├── __main__.py    # `python -m fourier_shapes` entry point
├── signals.py     # Path resampling and normalization
├── geo.py         # Natural Earth country loader (cached)
├── shapes.py      # Built-in parametric shapes + unified provider
├── fourier.py     # DFT decomposition and epicycle evaluation
└── app.py         # Matplotlib UI and animation loop
```

Each module is under 150 lines. The math (`fourier.py`, `signals.py`) is decoupled from both the data layer (`shapes.py`, `geo.py`) and the UI (`app.py`), so you can import just the pieces you need.

---

## 🎨 Supported Shapes

**Built-in parametric (7):**

`circle` · `square` · `triangle` · `star` · `heart` · `arrow` · `spiral`

**Countries (~60), matched case-insensitively with fuzzy substring fallback:**

`united states` · `china` · `russia` · `brazil` · `japan` · `france` · `germany` · `india` · `canada` · `australia` · `mexico` · `uk` · `south africa` · `argentina` · `egypt` · `turkey` · `nigeria` · `indonesia` · `thailand` · `sweden` · `norway` · `poland` · `ukraine` · `iran` · `iraq` · `saudi arabia` · `colombia` · `peru` · `venezuela` · `chile` · `kazakhstan` · `mongolia` · `south korea` · `north korea` · `vietnam` · `malaysia` · `philippines` · `pakistan` · `afghanistan` · `algeria` · `angola` · `mali` · `ethiopia` · `mozambique` · `madagascar` · `new zealand` · `bolivia` · `paraguay` · `uruguay` · `cuba` · `portugal` · `greece` · `romania` · `finland` · `denmark` · …

Both `united states of america` and `usa` resolve to the same country. See [`fourier_shapes/geo.py`](fourier_shapes/geo.py) for the full alias table.

---

## 🛣️ Roadmap

Ideas worth exploring (no promises, no timelines):

- [ ] Export animations as GIF / MP4
- [ ] Import your own SVG paths
- [ ] Pause / scrub / reverse controls
- [ ] More geography — US states, constellations, hand-drawn glyphs
- [ ] Web version (p5.js or WebGL) for share-a-link demos

Have an idea? Open an issue.

---

## 🤝 Contributing

Contributions are welcome and the bar is low — this is a small hobby project, not a ceremony.

1. **Fork** the repo
2. **Branch** from `main`
3. **Change** the thing
4. **Open a pull request** with a short description of what and why

### Adding a new built-in shape

Add a `make_<name>(n)` function to `fourier_shapes/shapes.py` that returns a length-`n` complex `numpy` array (`x + 1j*y`), then register it in the `BUILTIN_SHAPES` dict. That's it — the rest of the pipeline picks it up automatically.

### Adding a new country alias

Edit the `GEO_SHAPES` dict in `fourier_shapes/geo.py` — the keys are lowercased user input, the values are the canonical name used by Natural Earth.

---

## 📜 License

Released under the [MIT License](LICENSE). Do what you like with it.

© 2026 [Evan McCall](https://github.com/Evan-McCall)

---

<div align="center">

Built with `numpy`, `matplotlib`, and a bit of complex analysis.<br>
If this helped a concept click for you, please ⭐ the repo.

</div>
