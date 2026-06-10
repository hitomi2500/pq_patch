import itertools
from PIL import Image, ImageDraw, ImageFont
import os
import sys
import pycdlib
import math
import numpy
import  pickle
from pq_charset import PQ_Charset

def is_power_of_two(n):
    """
    Checks if a positive integer is a power of two using bitwise operations.
    Returns True for n=1 (2^0). Excludes n <= 0.
    """
    return n > 0 and (n & (n - 1)) == 0

def rgb555_palette_to_rgb_list(data: bytes):
    """
    Convert RGB555 palette bytes into a list of [R, G, B] values (0-255).
    Assumes little-endian 16-bit RGB555 entries.
    """
    result = []

    for i in range(0, len(data), 2):
        value = int.from_bytes(data[i:i+2], "big")

        b5 = (value >> 10) & 0x1F
        g5 = (value >> 5) & 0x1F
        r5 = value & 0x1F

        # Expand 5-bit to 8-bit
        r = (r5 << 3) | (r5 >> 2)
        g = (g5 << 3) | (g5 >> 2)
        b = (b5 << 3) | (b5 >> 2)

        result.append([r, g, b])

    return result

filename_iso = 'D:\\Saturn\\PrincessQuest\\ISO\\Princess Quest (Japan).iso'   
output_folder = 'sprites'

if not os.path.exists(str(filename_iso)):
    print(f"Cannot find file : {filename_iso}\n")
    print(f"Try running bit_2_iso.py first\n")
    sys.exit(0)

os.makedirs(output_folder, exist_ok=True)

# Open the ISO image in read mode
iso = pycdlib.PyCdlib()
iso.open(filename_iso)

pq_charset = PQ_Charset("pq_charset.toml")

#text = pq_charset.decode(b"\x00\x10\x00\x11")
#raw = pq_charset.encode("test")

for child in iso.list_children(iso_path='/'):
    file_name = child.file_identifier().decode('utf-8').replace(';1','')
    if not 'BIND' in file_name:
        continue
    if not '.DATa' in file_name:
        continue

    #parse tbl first
    with iso.open_file_from_iso(iso_path='/'+child.file_identifier().decode('utf-8').replace('.DAT','.TBL')) as input_file_tbl:
        print(f"File: {file_name}")
        input_content_tbl = input_file_tbl.read()             
        #parsing tbl
        tbl_index = 0
        subfiles = list()
        while (tbl_index < len(input_content_tbl)):
            bind_file_name = input_content_tbl[tbl_index:tbl_index+8].decode('latin1')+'.'+input_content_tbl[tbl_index+8:tbl_index+11].decode('latin1')
            bind_file_name = bind_file_name.replace(" ", "")
            #if not '.ACM' in bind_file_name:
            #    print(int.from_bytes(input_content_tbl[tbl_index+11:tbl_index+15], byteorder='big'))
            #    print(int.from_bytes(input_content_tbl[tbl_index+14:tbl_index+19], byteorder='big'))
            bind_file_start = int.from_bytes(input_content_tbl[tbl_index+11:tbl_index+15], byteorder='big')
            bind_file_size = int.from_bytes(input_content_tbl[tbl_index+15:tbl_index+19], byteorder='big')
            tbl_index+=19
            subfiles.append((bind_file_name,bind_file_start,bind_file_size))
            #print(input_content_tbl[0:8])
            #print(f"File:  {file_name} subfile {bind_file_name} start {bind_file_start} end {bind_file_end}")

    #now parse dat for each tbl entry
    with iso.open_file_from_iso(iso_path='/'+child.file_identifier().decode('utf-8')) as input_file:
        input_content = input_file.read()

        for subfile in subfiles:
            if '.B8' in subfile[0]:
                #searching corresponding pal
                searchname = subfile[0].replace('.B8','.PAL')
                #print(searchname)
                palette = next((item for item in subfiles if searchname in item), None)
                if (palette != None):
                    #print(f"FOUND!!!!!!!!!!: {subfile[0]} palette {palette[0]}")
                    #get palette
                    palette_rgb = rgb555_palette_to_rgb_list(input_content[palette[1]:palette[1]+palette[2]])
                    #genearte numpy from image
                    sublen = subfile[2]
                    sub_x = 640
                    if (sublen in {3584}): sub_x = 56
                    if (sublen in {6400}): sub_x = 80
                    if (sublen in {46400}): sub_x = 200
                    if (sublen in {71680,74240}): sub_x = 320
                    sub_y = int(sublen/sub_x)+1
                    rgb_array = numpy.zeros((sub_y, sub_x, 3), dtype=numpy.uint8)
                    pixels = bytes(input_content[subfile[1]:subfile[1]+subfile[2]])
                    print(f"{subfile[0]}:{subfile[1]},{subfile[2]},{sub_x}x{sub_y}, {len(pixels)}")
                    for index,pixel in enumerate(pixels):
                        rgb_array[int((index)/sub_x),int((index)%sub_x)] = palette_rgb[pixel]
                    #rgb_array[:, :] = [255, 128, 0]  # Fill with an orange color
                    img = Image.fromarray(rgb_array)#, mode="RGB")
                    img.save(output_folder+'/'+file_name+'_'+subfile[0]+'.png')
            
            if '.B16' in subfile[0]:
                #genearte numpy from image
                sublen = subfile[2]
                sub_x = 640
                #if (sublen in {3584}): sub_x = 56
                #if (sublen in {6400}): sub_x = 80
                if (sublen in {22528}): sub_x = 128
                if (sublen in {143360,153600}): sub_x = 320
                sub_y = int(sublen/(sub_x*2))+1
                rgb_array = numpy.zeros((sub_y, sub_x, 3), dtype=numpy.uint8)
                pixels = bytes(input_content[subfile[1]:subfile[1]+subfile[2]])
                colors = rgb555_palette_to_rgb_list(pixels)
                print(f"{subfile[0]}:{subfile[1]},{subfile[2]},{sub_x}x{sub_y}, {len(pixels)}")
                for index,color in enumerate(colors):
                    rgb_array[int((index)/sub_x),int((index)%sub_x)] = color
                #rgb_array[:, :] = [255, 128, 0]  # Fill with an orange color
                img = Image.fromarray(rgb_array)#, mode="RGB")
                img.save(output_folder+'/'+file_name+'_'+subfile[0]+'.png')



#now non-bind sprites

for child in iso.list_children(iso_path='/'):
    file_name = child.file_identifier().decode('utf-8').replace(';1','')
    if not '.B8' in file_name:
        continue
    with iso.open_file_from_iso(iso_path='/'+child.file_identifier().decode('utf-8')) as input_file:
        input_content = input_file.read()
        pal_name = file_name.replace('.B8','.PAL')
        with iso.open_file_from_iso(iso_path='/'+pal_name+';1') as pal_file:
            #get palette
            pal_content = pal_file.read()
            palette_rgb = rgb555_palette_to_rgb_list(pal_content)
            #genearte numpy from image
            sublen = len(input_content)
            sub_x = 320
            #if (sublen in {71680,74240}): sub_x = 320
            sub_y = int(sublen/sub_x)+1
            rgb_array = numpy.zeros((sub_y, sub_x, 3), dtype=numpy.uint8)
            pixels = bytes(input_content)
            print(f"{file_name}:{sublen},{sub_x}x{sub_y}, {len(pixels)}")
            for index,pixel in enumerate(pixels):
                rgb_array[int((index)/sub_x),int((index)%sub_x)] = palette_rgb[pixel]
            #rgb_array[:, :] = [255, 128, 0]  # Fill with an orange color
            img = Image.fromarray(rgb_array)#, mode="RGB")
            img.save(output_folder+'/'+file_name+'.png')

for child in iso.list_children(iso_path='/'):
    file_name = child.file_identifier().decode('utf-8').replace(';1','')
    if not '.B16' in file_name:
        continue
    with iso.open_file_from_iso(iso_path='/'+child.file_identifier().decode('utf-8')) as input_file:
        input_content = input_file.read()
        #genearte numpy from image
        sublen = len(input_content)
        sub_x = 640
        sub_y = int(sublen/(sub_x*2))+1
        rgb_array = numpy.zeros((sub_y, sub_x, 3), dtype=numpy.uint8)
        colors = rgb555_palette_to_rgb_list(input_content)
        print(f"{file_name}:{sublen},{sub_x}x{sub_y}")
        for index,color in enumerate(colors):
            rgb_array[int((index)/sub_x),int((index)%sub_x)] = color
        #rgb_array[:, :] = [255, 128, 0]  # Fill with an orange color
        img = Image.fromarray(rgb_array)#, mode="RGB")
        img.save(output_folder+'/'+file_name+'.png')