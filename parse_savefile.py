#!/usr/bin/env python3

import os
import sys
import zlib
import time
import json
import struct
from PIL import Image
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count
from collections import namedtuple

# fmt: off
colors = {
    1:  (200, 200, 200, 255),
    2:  (80,  140, 50,  255),
    3:  (150, 100, 50,  255),
    4:  (175, 175, 175, 255),
    5:  (192, 150, 96,  255),
    6:  (70,  180, 40,  255),
    8:  (0,   0,   200, 255),
    9:  (0,   0,   200, 255),
    10: (255, 150, 0,   255),
    11: (255, 150, 0,   255),
    12: (255, 255, 200, 255),
    13: (170, 150, 170, 255),
    14: (255, 255, 96,  255),
    15: (200, 180, 150, 255),
    16: (80,  80,  80,  255),
    17: (192, 150, 96,  255),  # copy of 5
    18: (0,   75,  0,   255),
    24: (255, 255, 200, 255),  # copy of 12
    26: (140, 25,  25,  255),

    31: (60,  120, 60,  255),  # grass? shrub?
    32: (60,  120, 60,  255),  # grass? shrub?

    35: (255, 255, 255, 255),
    37: (255, 255, 50,  255),
    38: (255, 0,   0,   255),
    39: (200, 150, 120, 255),
    40: (180, 50,  50,  255),
    44: (200, 200, 200, 255),  # copy of 1
    48: (115, 127, 115, 255),
    49: (20,  20,  30,  255),
    50: (255, 255, 50,  255),
    51: (255, 150, 0,   255),  # copy of 10
    52: (60,  90,  180, 255),
    53: (192, 150, 96,  255),  # copy of 5
    54: (192, 150, 96,  255),  # copy of 5
    58: (192, 150, 96,  255),  # copy of 5
    61: (200, 200, 200, 255),  # copy of 1
    63: (192, 150, 96,  255),  # copy of 5
    65: (192, 150, 96,  255),  # copy of 5
    67: (175, 175, 175, 255),  # copy of 4
    78: (255, 255, 255, 255),
    79: (128, 192, 255, 255),
    81: (10,  100, 25,  255),
    82: (222, 222, 255, 255),
    83: (150, 250, 150, 255),
    85: (192, 150, 96,  255),  # copy of 5
    86: (255, 144, 0,   255),
    91: (255, 144, 0,   255),  # copy of 86
}
# fmt: on

TAG_End = 0
TAG_Byte = 1
TAG_Short = 2
TAG_Int = 3
TAG_Long = 4
TAG_Float = 5
TAG_Double = 6
TAG_Byte_Array = 7
TAG_String = 8
TAG_List = 9
TAG_Compound = 10
TAG_Int_Array = 11
TAG_Long_Array = 12

Job = namedtuple(
    "Job",
    [
        "inFile",  # input file
        "outFile",  # output file
        "jobs_total",  # total count
        "job_id",  # current item
        "regionCoords",  # region coordinates
    ],
)


def read_file(mcr_path):
    # accepts path to file
    # reads this file
    # returns a list of chunks (nbt data as byte strings) from that file

    with open(mcr_path, "rb") as f:
        fraw = f.read()

    chunks = list(
        filter(
            lambda c: c["ofs"],
            [
                {
                    # offset from start of file
                    "ofs": 4096 * ((fraw[i] << 16) + (fraw[i + 1] << 8) + fraw[i + 2]),
                    #
                    # how many sectors the chunk occupies in the file.
                    # Dont need this. Each chunk data is preceded by a length field
                    # 'sectors': fraw[i+3],
                    #
                    # chunk last modified time
                    "time": struct.unpack(">I", fraw[i + 4096 : i + 4100])[0],
                }
                for i in range(0, 4096, 4)
            ],
        )
    )

    for c in chunks:
        assert 2 == fraw[c["ofs"] + 4]  # fail if compression is not Zlib
        size = struct.unpack(">I", fraw[c["ofs"] : c["ofs"] + 4])[0]
        c["raw"] = zlib.decompress(fraw[c["ofs"] + 5 : c["ofs"] + 5 + size])
        del c["ofs"]

    return chunks


def parse_nbt(raw, ofs, overrideMeta=None):
    # accepts binary nbt data
    # returns an object representing the nbt data

    if overrideMeta == None:
        typeID = raw[ofs]
        ofs += 1

        namelen = struct.unpack(">H", raw[ofs : ofs + 2])[0]
        ofs += 2

        name = raw[ofs : ofs + namelen].decode("utf8")
        ofs += namelen
    else:
        typeID = overrideMeta
        name = "UNNAMED"

    if typeID == TAG_Byte:
        ndata = struct.unpack(">b", raw[ofs : ofs + 1])[0]
        ofs += 1

    elif typeID == TAG_Short:
        ndata = struct.unpack(">h", raw[ofs : ofs + 2])[0]
        ofs += 2

    elif typeID == TAG_Int:
        ndata = struct.unpack(">i", raw[ofs : ofs + 4])[0]
        ofs += 4

    elif typeID == TAG_Long:
        ndata = struct.unpack(">q", raw[ofs : ofs + 8])[0]
        ofs += 8

    elif typeID == TAG_Float:
        ndata = struct.unpack(">f", raw[ofs : ofs + 4])[0]
        ofs += 4

    elif typeID == TAG_Double:
        ndata = struct.unpack(">d", raw[ofs : ofs + 8])[0]
        ofs += 8

    elif typeID == TAG_Byte_Array:
        arraysize = struct.unpack(">i", raw[ofs : ofs + 4])[0]
        assert arraysize >= 0
        ofs += 4
        ndata = raw[ofs : ofs + arraysize]
        ofs += arraysize

    elif typeID == TAG_String:
        stringsize = struct.unpack(">h", raw[ofs : ofs + 2])[0]
        assert stringsize >= 0
        ofs += 2
        ndata = raw[ofs : ofs + stringsize].decode("utf8")
        ofs += stringsize

    elif typeID == TAG_List:
        listContentsType = raw[ofs]
        ofs += 1
        count = struct.unpack(">i", raw[ofs : ofs + 4])[0]
        assert count >= 0
        ofs += 4
        ndata = []
        for _ in range(count):
            _, elem, ofs = parse_nbt(raw, ofs, overrideMeta=listContentsType)
            ndata.append(elem)

    elif typeID == TAG_Compound:
        ndata = dict()
        while raw[ofs]:
            elemName, elemData, ofs = parse_nbt(raw, ofs)
            assert not elemName in ndata  # I dont think duplicates happen
            ndata[elemName] = elemData
        ofs += 1

    else:
        raise Exception("Unknown NBT Tag (%i)!" % typeID)

    return name, ndata, ofs


def fileWorker(j):
    # accepts a "job"
    # reads input file. writes output file
    # returns ([bed1,bed2],[sign1,sign2])

    bed_list = []
    sign_list = []

    print(f" progress: {j.job_id}/{j.jobs_total}", " " * 8, end="\r")

    img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    pixels = img.load()

    for chunk in read_file(j.inFile):
        _, level, _ = parse_nbt(chunk["raw"], 0)
        level = level["Level"]

        # If this region file is storing chunks from
        # outside of its region, we've got problems!
        assert level["xPos"] // 32 == j.regionCoords[0]
        assert level["zPos"] // 32 == j.regionCoords[1]

        # Signs are stored in level['TileEntities'].
        # Their rotation is stored somewhere else, but I don't need that.
        for s in level["TileEntities"]:
            if s["id"] == "Sign":
                sign = {
                    "time": chunk["time"],
                    "x": s["x"],
                    "z": s["z"],
                    "text": [
                        s["Text1"],
                        s["Text2"],
                        s["Text3"],
                        s["Text4"],
                    ],
                }
                if "".join(sign["text"]):
                    print("sign:", sign)
                    sign_list.append(sign)

        # beds are regular blocks (ID 0x1A), and their
        # rotation and head/foot info stored in level['Data'].
        if b"\x1a" in level["Blocks"]:
            chunk_beds = [
                {
                    "x": level["xPos"] * 16 + i // 2048,
                    "z": level["zPos"] * 16 + i // 128 % 16,
                    "time": chunk["time"],
                    # head (8) or foot (0) of bed:
                    "end": (level["Data"][i >> 1] >> (i % 2 * 4)) & 8,
                    # Bed orientation:
                    # 'rotate':
                    #   (level['Data'][i >> 1] >> (i % 2 * 4)) & 3,
                }
                for i, b in enumerate(level["Blocks"])
                if b == 0x1A
            ]

            for bed in chunk_beds:
                if bed["end"]:  # only count head of beds
                    del bed["end"]
                    print("bed:", bed)
                    bed_list.append(bed)

        # for every z,x coordinate in this chunk, find the surface block and
        # its color, and add the pixel to the PIL image.
        for z in range(16):
            for x in range(16):
                # HeightMap saves the highest block the sun reaches
                y = 128 * z + 2048 * x + level["HeightMap"][z * 16 + x] - 1

                # snow does not block light, so HeightMap ignores it.
                # check if block above is snow and use that instead.
                while y % 128 < 127 and level["Blocks"][y + 1]:
                    y += 1

                b = level["Blocks"][y]
                if b:
                    if b in colors:
                        color = colors[b]
                    else:
                        print("no color for block:", b, " " * 8, end="\n" * 4)
                        color = (255, 0, 127, 255)

                    pixels[
                        level["xPos"] % 32 * 16 + x, level["zPos"] % 32 * 16 + z
                    ] = color

    img.save(j.outFile, "png")

    return bed_list, sign_list


def tilesFromWorld(world_path):
    # accepts path to world folder
    # spawns file workers
    # outputs ./static/data/tiles_0 and ./static/data/data.json
    # returns nothing

    for p in ["./static/data", "./static/data/tiles_0"]:
        try:
            os.mkdir(p)
        except FileExistsError:
            pass

    regions = [
        list(map(int, x.split(".")[1:3])) for x in os.listdir(world_path + "/region")
    ]

    job_list = [
        Job(*x)
        for x in zip(
            map(lambda x: f"{world_path}/region/r.{x[0]}.{x[1]}.mcr", regions),
            map(lambda x: f"./static/data/tiles_0/r.{x[0]}.{x[1]}.png", regions),
            (len(regions),) * len(regions),
            range(len(regions)),
            regions,
        )
    ]

    with ProcessPoolExecutor(max_workers=cpu_count()) as pool:
        job_results = pool.map(fileWorker, job_list)
    print("")

    bed_list, sign_list = map(lambda x: sum(x, []), zip(*job_results))

    with open("./static/data/data.json", "w") as f:
        f.write(
            json.dumps(
                {
                    "beds": bed_list,
                    "signs": sign_list,
                    "tiles": {0: regions},
                }
            )
        )


if __name__ == "__main__":
    if len(sys.argv) == 2:
        tilesFromWorld(sys.argv[1])
    else:
        print("Please specify a world directory.")
