#!/usr/bin/env python3
import os
import json
from PIL import Image
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count

colors = {
    1: (200, 200, 200, 255),
    2: (60, 180, 60, 255),
    3: (150, 100, 50, 255),
    4: (175, 175, 175, 255),
    5: (192, 150, 96, 255),
    8: (0, 0, 200, 255),
    9: (0, 0, 200, 255),
    10: (255, 150, 0, 255),
    11: (255, 150, 0, 255),
    12: (255, 255, 200, 255),
    13: (170, 150, 170, 255),
    15: (200, 180, 150, 255),
    16: (80, 80, 80, 255),
    17: (192, 150, 96, 255),
    18: (0, 75, 0, 255),
    24: (255, 255, 200, 255),
    44: (175, 175, 175, 255),
    49: (20, 20, 30, 255),
    67: (175, 175, 175, 255),
    78: (255, 255, 255, 255),
    79: (128, 192, 255, 255),
    82: (222, 222, 255, 255),
    86: (255, 144, 0, 255),
}


def worker(job):
    print(f' progress {job[1]}/{job[2]}', ' '*8, end='\r')
    tile = job[0]

    img = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
    pixels = img.load()
    with open(f'./data/raw_tile_data/r.{tile[0]}.{tile[1]}.dat', 'rb') as f:
        for i, b in enumerate(f.read()):
            if b:
                if b in colors:
                    color = colors[b]
                else:
                    print('no color for block:', b, ' '*8)
                    color = (255, 0, 127, 255)
                pixels[i % 512, i//512] = color
    img.save(f'./data/tiles_1/r.{tile[0]}.{tile[1]}.png', "png")


try:
    os.mkdir('./data/tiles_1')
except FileExistsError:
    pass

with open('./data/tiles_1.json') as f:
    tiles = json.loads(f.read())

jobs = list(zip(
    # tile coords
    tiles,
    # current item
    range(len(tiles)),
    # total items
    (len(tiles),) * len(tiles),
))

with ProcessPoolExecutor(max_workers=cpu_count()) as pool:
    list(pool.map(worker, jobs))

print('')
