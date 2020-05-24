#!/usr/bin/env python3
import os
import math
import json
from PIL import Image
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count


def squashCoord(x):
    # given source tile coords, find the destination tile it belongs in
    return (x[0]//2, x[1]//2)


def expandCoord(x):
    # given destination tile coords, find the source tiles it should
    # contain and position they sould be within the destination tile
    return (
        (x[0]*2, x[1]*2, 0, 0),
        (x[0]*2+1, x[1]*2, 256, 0),
        (x[0]*2, x[1]*2+1, 0, 256),
        (x[0]*2+1, x[1]*2+1, 256, 256),
    )


def worker(job):
    tile, zoom, current, total = job
    print(f' progress {current}/{total}', ' '*8, end='\r')
    dst = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
    for srcX, srcY, dstX, dstY in expandCoord(tile):
        if [srcX, srcY] in intTileList:
            src = Image.open(f'./data/tiles_{zoom//2}/r.{srcX}.{srcY}.png')
            dst.paste(src.resize((256, 256)), (dstX, dstY))

    dst.save(f'./data/tiles_{zoom}/r.{tile[0]}.{tile[1]}.png', 'png')


with ProcessPoolExecutor(max_workers=cpu_count()) as pool:
    for zoom in [2]:
        print('\nProcessing Zoom Level', zoom)

        intTileList = json.loads(f.read())
        with open(f'./data/tiles_{zoom//2}.json') as f:
            outTileList = list(set(map(squashCoord, intTileList)))

        try:
            os.mkdir(f'./data/tiles_{zoom}')
        except FileExistsError:
            pass

        jobs = list(zip(
            # tile to generate
            outTileList,
            # current zoom level
            (zoom,) * len(outTileList),
            # current item
            range(len(outTileList)),
            # total items
            (len(outTileList),) * len(outTileList),
        ))

        list(pool.map(worker, jobs))

        with open(f'./data/tiles_{zoom}.json', 'w') as f:
            f.write(json.dumps(outTileList))
print('')
