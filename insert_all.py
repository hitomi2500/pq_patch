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

use_verify = 0
font_file = 'font.png'

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

        #print(child.file_identifier().decode('utf-8'))
        new_fp = io.BytesIO(output_content)
        iso_patched.modify_file_in_place(new_fp, len(output_content), "/KANJI.FON;1")

#patching A.BIN
with iso_patched.open_file_from_iso(iso_path="/A.BIN;1") as input_file:
    input_content = input_file.read() 
    print(len(input_content))

        # #counting chars
        # chars = int(len(input_content)/32)
        # print(f"Total chars: {chars}")

        # table_x = int(math.sqrt(chars))
        # while (False == is_power_of_two(table_x)):
        #     table_x = table_x + 1
        # table_y = int((chars-1)/table_x)+1

        # font_size = 16

        # print(f"Font size {font_size},  chars {chars}, table {table_x}x{table_y}")

        # magenta_pattern = numpy.array([255, 0, 255], dtype=numpy.uint8)
        # black_pattern = numpy.array([0, 0, 0], dtype=numpy.uint8)
        # white_pattern = numpy.array([255, 255, 255], dtype=numpy.uint8)
        # array_data = numpy.empty(((table_y*(use_verify+1))*font_size,(table_x)*font_size,3), dtype=numpy.uint8)
        # array_data[:] = black_pattern
        # font = ImageFont.truetype("ttf/HinaMincho-Regular.ttf", font_size-3)
        # #canvas = Image.new("RGB", (font_size, font_size), color=0)
        # im = Image.new("RGB", (16, 16), "black")
        # draw = ImageDraw.Draw(im)
        # for current_index in range(chars):
        #     char_x = int(current_index%table_x)
        #     char_y = int(current_index/table_x)
        #     for y in range(16):
        #         for x in range(16):
        #             if (input_content[current_index*32+y*2+int(x/8)] & (1<<(7-x%8))):
        #                 array_data[char_y*16*(use_verify+1)+y][char_x*16+x] = white_pattern

        # #saving image
        # img = Image.fromarray(array_data)#, 'RGB')
        # img.save(output_folder + '/' + file_name + ".png")

        # with open(output_folder + '/' + file_name, "wb") as file:
        #     file.write(bytearray(input_content))

        # 