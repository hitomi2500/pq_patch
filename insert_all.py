import itertools
from PIL import Image, ImageDraw, ImageFont
import os
import sys
import pycdlib
import math
import numpy
import shutil
import  pickle
from pq_charset import PQ_Charset
import io
import tomllib

use_verify = 0

def is_power_of_two(n):
    """
    Checks if a positive integer is a power of two using bitwise operations.
    Returns True for n=1 (2^0). Excludes n <= 0.
    """
    return n > 0 and (n & (n - 1)) == 0

filename_iso = 'D:\\Saturn\\PrincessQuest\\ISO\\Princess Quest (Japan).iso'   
filename_iso_patched = 'D:\\Saturn\\PrincessQuest\\ISO\\Princess Quest (Japan) (Patched).iso'   

if not os.path.exists(str(filename_iso)):
    print(f"Cannot find file : {filename_iso}\n")
    print(f"Try running bit_2_iso.py first\n")
    sys.exit(0)

#(re)creating the patched copy
if os.path.exists(filename_iso_patched):
    os.remove(filename_iso_patched)
shutil.copyfile(filename_iso,filename_iso_patched)

# Open the ISO image in read mode
#iso = pycdlib.PyCdlib()
#iso.open(filename_iso)
iso_patched = pycdlib.PyCdlib()
iso_patched.open(filename_iso_patched,'r+b')

#patching font file
font_file = 'font.png'
with iso_patched.open_file_from_iso(iso_path="/KANJI.FON;1") as input_file:
    input_content = input_file.read() 
    output_content = bytearray(input_content)
    if os.path.isfile(font_file):
        img = Image.open(font_file)
        img_array = numpy.asarray(img)
        print(f"Updating KANJI.FON with {font_file} content")
        #print(img.size)
        for char in range(0x60):
            char_font = char + 0x20
            for y in range(16):
                for x in range(8):
                    if (int(int(char%16)*8+x)>127):
                        print(f"shit x! {char} {x} {y} {int(int(char%16)*8+x)}")
                    if (int(int(char/16)*16+y)>95):
                        print(f"shit y! {char} {x} {y} {int(int(char/16)*16+y)}")
                    if (img_array[int(int(char/16)*16+y)][int((char%16)*8+x)] != 0):
                        output_content[int(char_font*32 + y*2)] = output_content[char_font*32 + y*2] | 1<<(7-x)
                    else:
                        output_content[int(char_font*32 + y*2)] = output_content[char_font*32 + y*2] & (~(1<<(7-x)))
                    output_content[int(char_font*32 + y*2 + 1)] = 0 #unused right half of char
        new_fp = io.BytesIO(output_content)
        iso_patched.modify_file_in_place(new_fp, len(output_content), "/KANJI.FON;1")

#patching A.BIN
a_patch_file = 'A_patch.toml'
with iso_patched.open_file_from_iso(iso_path="/A.BIN;1") as input_file:
    input_content = input_file.read()
    output_content = bytearray(input_content)
    #print(len(input_content))
    with open(a_patch_file,"rb") as input_file:
        print(f"Patching A.BIN with {a_patch_file} content")
        patch_data = tomllib.load(input_file)
        for c in patch_data["change"]:
            offset = int(c["offset"])
            old = bytes(c["old"])
            new = bytes(c["new"])
            size = len(new)
            assert (len(new)==len(old))
            if (input_content[offset:offset+size] != old):
                print(f"Patch error at {offset:x}: old content ({input_content[offset:offset+size]}) != patch old ({old})")
            else:
                output_content[offset:offset+size] = new        
        new_fp = io.BytesIO(output_content)
        iso_patched.modify_file_in_place(new_fp, len(output_content), "/A.BIN;1")

#patching PRO01.MES
with iso_patched.open_file_from_iso(iso_path="/PRO01.MES;1") as input_file:
    input_content = input_file.read()
    output_content = bytearray(input_content)
    #test patching vocabulary
    for i in range(32):
        output_content[2+i*2] = 0x81
        output_content[2+i*2+1] = 0x80+i
    output_content[2+32*2] = 0x81
    output_content[2+32*2+1] = 0x7F
    offsettt = 0x41
    output_content[0x68ec] = ord('L')+offsettt
    output_content[0x68ed] = ord('O')+offsettt
    output_content[0x68ee] = ord('R')+offsettt
    output_content[0x68ef] = ord('E')+offsettt
    output_content[0x68f0] = ord('E')+offsettt
    output_content[0x68f1] = ord('M')+offsettt
    output_content[0x68f2] = ord('A')+offsettt-1
    output_content[0x68f3] = ord('I')+offsettt
    output_content[0x68f4] = ord('P')+offsettt
    output_content[0x68f5] = ord('S')+offsettt
    output_content[0x68f6] = ord('U')+offsettt
    output_content[0x68f7] = ord('M')+offsettt
    output_content[0x68f8] = ord('A')+offsettt-1
    output_content[0x68f9] = ord('D')+offsettt
    output_content[0x68fa] = ord('O')+offsettt
    output_content[0x68fb] = ord('L')+offsettt
    output_content[0x68fc] = ord('O')+offsettt
    output_content[0x68fd] = ord('R')+offsettt
    #output_content[0x68fe] = ord('!')+offsettt
    new_fp = io.BytesIO(output_content)
    iso_patched.modify_file_in_place(new_fp, len(output_content), "/PRO01.MES;1")
