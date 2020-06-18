# MCBetaMap
A map generator for Minecraft 1.7.3 worlds

## Requirements
Python 3.7 or greater. Python for Windows can be downloaded from python.org

---

## Usage
**Depending on your platform, you may need to substitute the "python" command with "python3".**

The following commands are required only once, to install the Pillow image processing library.
```
python -m pip install --user --upgrade setuptools
python -m pip install --user --upgrade Pillow
```

The following commands will generate map data from a Minecraft world.

These commands must be run from a terminal/cmd window open inside the mcbetamap directory.
```
python ./parse_savefile.py "<Path to Minecraft world>"
python ./create_zoom_tiles.py
```

The world path may be in the form `"~/.minecraft/saves/testworld/"` on Linux,

or `"C:\Users\me\AppData\Roaming\.minecraft\saves\testworld\"` on Windows.