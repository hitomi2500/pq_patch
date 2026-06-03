import itertools
from PIL import Image, ImageDraw, ImageFont
import os
import sys
import pycdlib
import math
import numpy
import  pickle
from pq_charset import PQ_Charset

use_verify = 0

def is_power_of_two(n):
    """
    Checks if a positive integer is a power of two using bitwise operations.
    Returns True for n=1 (2^0). Excludes n <= 0.
    """
    return n > 0 and (n & (n - 1)) == 0

filename_iso = 'D:\\Saturn\\PrincessQuest\\ISO\\Princess Quest (Japan).iso'   
output_folder = 'font'

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
    if not '.FON' in file_name:
        continue
    
    with iso.open_file_from_iso(iso_path='/'+child.file_identifier().decode('utf-8')) as input_file:
        input_content = input_file.read() 

        print(f"File: {file_name}")

        #counting chars
        chars = int(len(input_content)/32)
        print(f"Total chars: {chars}")

        table_x = int(math.sqrt(chars))
        while (False == is_power_of_two(table_x)):
            table_x = table_x + 1
        table_y = int((chars-1)/table_x)+1

        font_size = 16

        print(f"Font size {font_size},  chars {chars}, table {table_x}x{table_y}")

        magenta_pattern = numpy.array([255, 0, 255], dtype=numpy.uint8)
        black_pattern = numpy.array([0, 0, 0], dtype=numpy.uint8)
        white_pattern = numpy.array([255, 255, 255], dtype=numpy.uint8)
        array_data = numpy.empty(((table_y*(use_verify+1))*font_size,(table_x)*font_size,3), dtype=numpy.uint8)
        array_data[:] = black_pattern
        font = ImageFont.truetype("ttf/HinaMincho-Regular.ttf", font_size-3)
        #canvas = Image.new("RGB", (font_size, font_size), color=0)
        im = Image.new("RGB", (16, 16), "black")
        draw = ImageDraw.Draw(im)
        for current_index in range(chars):
            char_x = int(current_index%table_x)
            char_y = int(current_index/table_x)
            for y in range(16):
                for x in range(16):
                    if (input_content[current_index*32+y*2+int(x/8)] & (1<<(7-x%8))):
                        array_data[char_y*16*(use_verify+1)+y][char_x*16+x] = white_pattern

            #verify kanji
            if use_verify:
                draw.rectangle([(0, 0), (16, 16)], fill="black")
                sjis_bytes = (current_index+0x8140).to_bytes(2, byteorder='big')
                #sjis_bytes = b'\x82\xb1'
                try:
                    #decoded_string = sjis_bytes.decode('shift_jis')
                    decoded_string = pq_charset.decode(current_index.to_bytes(2, byteorder='big'))
                except UnicodeDecodeError:
                    decoded_string = ""
                    if (current_index%4 == 0):
                        decoded_string = "0x"
                    elif (current_index%4 == 1):
                        decoded_string = f"{int(current_index/0x100):X}"
                    elif (current_index%4 == 2):
                        decoded_string = f"{int(current_index%0x100):X}"
                
                print(current_index)
                draw.text(xy=(0,0), text=decoded_string, font=font, fill=(255,255,0) )
                #print(decoded_string)
                for y in range(16):
                    for x in range(16):
                        pixel = im.getpixel((x, y))
                        #if (pixel[0]):
                        #    print(pixel)
                        array_data[char_y*16*2+16+y][char_x*16+x] = numpy.array([pixel[0], pixel[1], pixel[2]], dtype=numpy.uint8)


        #saving image
        img = Image.fromarray(array_data)#, 'RGB')
        img.save(output_folder + '/' + file_name + ".png")

        with open(output_folder + '/' + file_name, "wb") as file:
            file.write(bytearray(input_content))