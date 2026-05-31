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

filename_iso = 'D:\\Saturn\\PrincessQuest\\ISO\\Princess Quest (Japan).iso'   
output_folder = 'mes'

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
    if not '.MES' in file_name:
        continue
    
    with iso.open_file_from_iso(iso_path='/'+child.file_identifier().decode('utf-8')) as input_file:
        input_content = input_file.read() 

        print(f"File: {file_name}")

        vocabulary_size = (input_content[0] + input_content[1]*0x100 - 2)>>1
        print(f"Vocabulary size: {vocabulary_size}")

        #reading vocabulary
        vocabulary = dict()
        for i in range(vocabulary_size):
            vocabulary[i] = bytearray([input_content[i*2+2],input_content[i*2+3]])
            a = int.from_bytes(vocabulary[i],'big')
            if ((a<0x7FFF)&(a!=0)):
                print(f"Wrong vocab entry at {i} : {vocabulary[i]}")
                sys.exit()

        #extend vocabulary to 256
        for i in range(vocabulary_size,256):
            vocabulary[i] = bytearray([0, 0])

        #recode output content
        output_content = bytearray()
        for i in range(vocabulary_size*2+2,len(input_content)):
            code = input_content[i]            
            #print(code)
            output_content += vocabulary[code]

        # #saving data
        with open(output_folder + '/' + file_name + '.sjis.txt', "wb") as file:
            file.write(output_content)