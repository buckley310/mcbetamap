#!/usr/bin/env python3

import os
import sys
import zlib
import time
import json
import struct
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count

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


def read_file(mcr_path):
    # accepts path to file
    # reads this file
    # returns a list of chunks (byte strings) from that file

    with open(mcr_path, 'rb') as f:
        fraw = f.read()

    chunks = list(filter(lambda c: c['ofs'], [
        {
            # offset from start of file
            'ofs': 4096 * ((fraw[i] << 16)+(fraw[i+1] << 8)+fraw[i+2]),

            # how many sectors the chunk occupies in the file.
            # Dont need this. Each chunk data is preceded by a length field
            # 'sectors': fraw[i+3],

            # chunk last modified time
            'time': struct.unpack('>I', fraw[i+4096:i+4100])[0],
        }
        for i in range(0, 4096, 4)
    ]))

    for c in chunks:
        assert 2 == fraw[c['ofs']+4]  # fail if compression is not Zlib
        size = struct.unpack('>I', fraw[c['ofs']:c['ofs']+4])[0]
        c['raw'] = zlib.decompress(fraw[c['ofs']+5:c['ofs']+5+size])
        del c['ofs']

    return chunks


def parse_nbt(raw, ofs, overrideMeta=None):
    # accepts binary nbt data
    # returns an object representing the nbt data

    if overrideMeta == None:
        typeID = raw[ofs]
        ofs += 1

        namelen = struct.unpack('>H', raw[ofs:ofs+2])[0]
        ofs += 2

        name = raw[ofs:ofs+namelen].decode('utf8')
        ofs += namelen
    else:
        typeID = overrideMeta
        name = 'UNNAMED'

    if typeID == TAG_Byte:
        ndata = struct.unpack('>b', raw[ofs:ofs+1])[0]
        ofs += 1

    elif typeID == TAG_Short:
        ndata = struct.unpack('>h', raw[ofs:ofs+2])[0]
        ofs += 2

    elif typeID == TAG_Int:
        ndata = struct.unpack('>i', raw[ofs:ofs+4])[0]
        ofs += 4

    elif typeID == TAG_Long:
        ndata = struct.unpack('>q', raw[ofs:ofs+8])[0]
        ofs += 8

    elif typeID == TAG_Float:
        ndata = struct.unpack('>f', raw[ofs:ofs+4])[0]
        ofs += 4

    elif typeID == TAG_Double:
        ndata = struct.unpack('>d', raw[ofs:ofs+8])[0]
        ofs += 8

    elif typeID == TAG_Byte_Array:
        arraysize = struct.unpack('>i', raw[ofs:ofs+4])[0]
        assert arraysize >= 0
        ofs += 4
        ndata = raw[ofs:ofs+arraysize]
        ofs += arraysize

    elif typeID == TAG_String:
        stringsize = struct.unpack('>h', raw[ofs:ofs+2])[0]
        assert stringsize >= 0
        ofs += 2
        ndata = raw[ofs:ofs+stringsize].decode('utf8')
        ofs += stringsize

    elif typeID == TAG_List:
        listContentsType = raw[ofs]
        ofs += 1
        count = struct.unpack('>i', raw[ofs:ofs+4])[0]
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


def fileWorker(job):
    # accepts a "job"
    # reads input file. writes output file
    # returns ([bed1,bed2],[sign1,sign2])

    bed_list = []
    sign_list = []
    inFile, outFile, jobs_total, job_id, (regX, regZ) = job

    print(f' progress: {job_id}/{jobs_total}', ' '*8, end='\r')

    with open(outFile, 'wb+') as f:
        for chunk in read_file(inFile):
            _, level, _ = parse_nbt(chunk['raw'], 0)
            level = level['Level']

            # If this region file is storing chunks from
            # outside of its region, we've got problems!
            assert level['xPos'] // 32 == regX
            assert level['zPos'] // 32 == regZ

            # Signs are stored in level['TileEntities'].
            # Their rotation is stored somewhere else, but I don't need that.
            for s in level['TileEntities']:
                if s['id'] == 'Sign':
                    sign = {
                        'time': chunk['time'],
                        'x': s['x'],
                        'z': s['z'],
                        'text': [
                            s['Text1'],
                            s['Text2'],
                            s['Text3'],
                            s['Text4'],
                        ]
                    }
                    if ''.join(sign['text']):
                        print('sign:', sign)
                        sign_list.append(sign)

            # beds are regular blocks (ID 0x1A), and their
            # rotation and head/foot info stored in level['Data'].
            if b'\x1a' in level['Blocks']:
                chunk_beds = [
                    {
                        'x': level['xPos']*16 + i//2048,
                        'z': level['zPos']*16 + i//128 % 16,
                        'time': chunk['time'],
                        # head (8) or foot (0) of bed:
                        'end': (level['Data'][i >> 1] >> (i % 2 * 4)) & 8,
                        # Bed orientation:
                        # 'rotate':
                        #   (level['Data'][i >> 1] >> (i % 2 * 4)) & 3,
                    }
                    for i, b in enumerate(level['Blocks'])
                    if b == 0x1a
                ]

                for bed in chunk_beds:
                    if bed['end']:  # only count head of beds
                        del bed['end']
                        print('bed:', bed)
                        bed_list.append(bed)

            surface = []
            for z in range(16):
                for x in range(16):
                    # HeightMap saves the highest block the sun reaches
                    y = 128*z + 2048*x + level['HeightMap'][z*16+x] - 1

                    # snow does not block light, so HeightMap ignores it.
                    # check if block above is snow and use that instead.
                    if y & 0xff < 255 and level['Blocks'][y+1] == 78:
                        y += 1

                    surface.append(level['Blocks'][y])

            for y in range(16):
                f.seek(
                    (level['xPos'] % 32)*16 +
                    (level['zPos'] % 32)*8192 +
                    y*512
                )
                f.write(bytes(surface[y*16:y*16+16]))

    return bed_list, sign_list


def tilesFromWorld(world_path):
    # accepts path to world folder
    # spawns file workers
    # outputs raw_tiles.json, signs.json, beds.json
    # returns nothing

    try:
        os.mkdir('./data')
    except FileExistsError:
        pass
    try:
        os.mkdir('./data/raw_tiles')
    except FileExistsError:
        pass

    regions = [
        list(map(int, x.split('.')[1:3]))
        for x in os.listdir(world_path+'/region')
    ]

    job_list = list(zip(
        # input file
        map(lambda x: f'{world_path}/region/r.{x[0]}.{x[1]}.mcr', regions),
        # output file
        map(lambda x: f'./data/raw_tiles/r.{x[0]}.{x[1]}.dat', regions),
        # total count
        (len(regions) for _ in range(len(regions))),
        # current item
        (x for x in range(len(regions))),
        # region list
        regions,
    ))

    with ProcessPoolExecutor(max_workers=cpu_count()) as pool:
        job_results = pool.map(fileWorker, job_list)
    print('')

    bed_list, sign_list = map(lambda x: sum(x, []), zip(*job_results))

    with open('./data/raw_tiles.json', 'w') as f:
        f.write(json.dumps(regions))

    with open('./data/signs.json', 'w') as f:
        f.write(json.dumps(sign_list))

    with open('./data/beds.json', 'w') as f:
        f.write(json.dumps(bed_list))


if __name__ == "__main__":
    if len(sys.argv) == 2:
        tilesFromWorld(sys.argv[1])
    else:
        print("Please specify a world directory.")
