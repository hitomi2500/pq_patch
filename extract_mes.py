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

        #extend vocabulary to 128
        for i in range(vocabulary_size,128):
            vocabulary[i] = bytearray([0, 0])

        #recode output content
        output_content = bytearray()
        i = vocabulary_size*2+2
        #print(type(input_content))
        while (i<len(input_content)):
        #for i in range(vocabulary_size*2+2,len(input_content)):
            code = input_content[i]
            if (code in {0,1,2}):
                output_content += (bytes(f"<{code:x}>",'latin1'))
            elif (code in {3,5}):
                output_content += (bytes(f"<{code:x}>",'latin1'))
                #i+=1
                #code2 = input_content[i]
                #output_content += (bytes(f"<{code:x},{code2:x}>",'latin1'))
            elif (code == 4):
                i+=1
                code2 = input_content[i]
                if (code2 in {0x18,0x19,0x1b,0x1d,0x1e,0x1f,0x23}):
                    i+=1
                    code3 = input_content[i]
                    if (code3 == 0x6):
                        output_content += bytes(f'\r\n[LOAD{code2:x} ','latin1')
                        i+=1
                        while (input_content[i] != 6):
                            output_content += input_content[i:i+1]
                            i+=1
                        output_content += b']\r\n'
                        i+=1
                    else:
                        print(f"ERROR:WRONG LOAD, i = {i:x} code2 = {code2:x}")
                        output_content += (bytes(f"ERROR:WRONG LOAD, i = {i:x} code2 = {code2:x}",'latin1'))
                        #sys.exit(0)
                else:
                    output_content += (bytes(f"<{code:x}!!,{code2:x}>",'latin1'))
            elif (code == 6):
                output_content += b'\r\n[LOADold '
                i+=1
                while (input_content[i] != 6):
                    output_content += input_content[i:i+1]
                    i+=1
                output_content += b']\r\n'
                i+=1
            elif (code == 0xc):
                output_content += bytes(f"<{code:x}: ",'latin1')
                for j in range(3):
                    output_content += (bytes(f"{input_content[i+j+1]:x} ",'latin1'))
                output_content += b'>'
                i+=3
            elif (code == 0xd):
                output_content += bytes(f"<{code:x}: ",'latin1')
                for j in range(8):
                    output_content += (bytes(f"{input_content[i+j+1]:x} ",'latin1'))
                output_content += b'>'
                i+=8
            elif (code < 97):
                output_content += (bytes(f"<{code:x}>",'latin1'))
                #output_content += (bytes(f"<{i:x}>",'latin1'))
                code-=1
            elif (code < 128):
                output_content += (code+0x20).to_bytes(1)
                i=i+1
                code = input_content[i]
                output_content += code.to_bytes(1)
            else:
                code -= 128
                assert(code >=0)
                assert(code <=127)
                output_content += vocabulary[code]
            i+=1

        # #saving data
        with open(output_folder + '/' + file_name + '.sjis.txt', "wb") as file:
            file.write(output_content)