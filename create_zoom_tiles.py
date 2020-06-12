#!/usr/bin/env python3
import os
import math
import json
from PIL import Image
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count
from collections import namedtuple

Job = namedtuple('Job', [
    'tile',  # tile to generate
    'srcTiles',  # source tiles
    'zoom',  # current zoom level
    'current',  # current item
    'total',  # total items
])


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


def worker(j):
    print(f' progress {j.current}/{j.total}', ' '*8, end='\r')
    dst = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
    for srcX, srcY, dstX, dstY in expandCoord(j.tile):
        if [srcX, srcY] in j.srcTiles:
            src = Image.open(f'./data/tiles_{j.zoom//2}/r.{srcX}.{srcY}.png')
            src = src.resize((256, 256), resample=Image.NEAREST)
            dst.paste(src, (dstX, dstY))

    dst.save(f'./data/tiles_{j.zoom}/r.{j.tile[0]}.{j.tile[1]}.png', 'png')


def main():
    with open('./data/data.json') as f:
        mapData = json.loads(f.read())

    for zoom in [2, 4, 8, 16, 32, 64, 128, 256]:
        with ProcessPoolExecutor(max_workers=cpu_count()) as pool:
            print('\nProcessing Zoom Level', zoom)

            intTileList = mapData['tiles'][str(zoom//2)]
            outTileList = list(set(map(squashCoord, intTileList)))
            mapData['tiles'][str(zoom)] = outTileList

            try:
                os.mkdir(f'./data/tiles_{zoom}')
            except FileExistsError:
                pass

            jobs = [
                Job(*x) for x in zip(
                    outTileList,
                    (intTileList,) * len(outTileList),
                    (zoom,) * len(outTileList),
                    range(len(outTileList)),
                    (len(outTileList),) * len(outTileList),
                )
            ]

            list(pool.map(worker, jobs))

            mapData = json.loads(json.dumps(mapData))  # TODO: Remove this line

    with open('./data/data.json', 'w') as f:
        f.write(json.dumps(mapData))

    print('')


if __name__ == "__main__":
    main()