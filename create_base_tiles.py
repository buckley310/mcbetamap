#!/usr/bin/env python3
import os
from PIL import Image
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count

dir_in = './data/raw_tile_data'
dir_out = './data/tiles_1'

colors = {
    1: (200, 200, 200, 255),
    2: (60, 180, 60, 255),
    3: (150, 100, 50, 255),
    4: (175, 175, 175, 255),
    5: (180, 120, 0, 255),
    8: (0, 0, 200, 255),
    9: (0, 0, 200, 255),
    10: (255, 150, 0, 255),
    11: (255, 150, 0, 255),
    12: (255, 255, 200, 255),
    13: (170, 150, 170, 255),
    15: (200, 180, 150, 255),
    16: (80, 80, 80, 255),
    17: (180, 120, 0, 255),
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

try:
    os.mkdir(dir_out)
except FileExistsError:
    pass


def worker(job):
    filenum, fname = job
    print(' progress:', filenum, 'of', len(tileFiles), end='    \r')

    img = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
    pixels = img.load()
    with open(dir_in+'/'+fname, 'rb') as f:
        for i, b in enumerate(f.read()):
            if b:
                if b in colors:
                    color = colors[b]
                else:
                    print('no color for block:', b, ' '*8)
                    color = (255, 0, 127, 255)
                pixels[i % 512, i//512] = color
    img.save(dir_out+'/'+fname.replace('.dat', '.png'), "png")


tileFiles = os.listdir(dir_in)
with ProcessPoolExecutor(max_workers=cpu_count()) as pool:
    pool.map(worker, enumerate(tileFiles))
print('')
