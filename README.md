# Fourier Shapes

Type in a shape name and watch it get drawn by a chain of rotating circles (Fourier epicycles). Supports built-in shapes and any country outline from Natural Earth.

## What it does

Any closed 2D shape can be expressed as a sum of rotating complex exponentials — a Fourier series. This app:

1. Samples the outline of a shape into a complex signal.
2. Runs a DFT to decompose it into frequency components.
3. Animates each component as a rotating circle, with each circle's center riding on the tip of the previous one.
4. The tip of the last circle traces out the original shape.

A slider lets you add or remove circles live so you can see how adding higher-frequency terms sharpens the approximation.

## Shapes supported

- **Built-in:** `circle`, `square`, `triangle`, `star`, `heart`, `arrow`, `spiral`
- **Countries:** ~60 country names (e.g. `united states`, `japan`, `brazil`, `france`) — the outlines come from Natural Earth's 1:110m admin boundaries, downloaded and cached on first use into `~/.cache/fourier_shapes/`.

## Install

Requires Python 3.10+.

```bash
git clone https://github.com/Evan-McCall/fourier-shapes.git
cd fourier-shapes
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

`geopandas` pulls in `shapely`, `pyproj`, and `fiona`, which can take a minute to install.

## Run

```bash
python fourier_shapes.py
```

Type a shape name into the text box and hit Enter (or click **Generate**). Drag the **Circles** slider to change how many Fourier terms are drawn.

## Notes

- On macOS the app uses the `macosx` matplotlib backend for smoother animation. On Linux/Windows it falls back to the default backend (usually `TkAgg` or `Qt5Agg`) — you may need a GUI-capable backend installed.
- The first time you request a country, the app downloads ~1 MB of Natural Earth data from `naciscdn.org`.

## License

MIT
