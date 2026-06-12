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

filename_1_bin = 'D:\\Saturn\\PrincessQuest\\ISO\\Princess Quest (Japan) (Track 1).bin'   
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
    output_content = bytearray(input_content)#only using first 128 chars
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

#patching all .MES files
for child in iso_patched.list_children(iso_path='/'):
    file_name = child.file_identifier().decode('utf-8').replace(';1','')
    if not '.MES' in file_name:
        continue
    patch_name = "translation/"+file_name+".txt"
    #print(patch_name)
    if not os.path.exists(patch_name):
        continue
    print(f"Patching {file_name}")
    with iso_patched.open_file_from_iso(iso_path='/'+child.file_identifier().decode('utf-8')) as input_file:
        input_content = input_file.read()
        output_content = bytearray()
        with open(patch_name,'r') as transl_file:
            transl_str = transl_file.read().splitlines()
            #splitting content
            data_list = list()
            last_binary_ind = 0
            for line in transl_str:
                start = int(line.split(':')[0],16)
                end = int(line.split(':')[1],16)
                #data before text
                #data_list.append(last_binary_ind,input_content[last_binary_ind:start])
                output_content+=input_content[last_binary_ind:start]
                #now replacing the text
                #data_list.append(start,input_content[start:end+1])
                input_line = line.split(':')[2]
                for c in input_line:
                    #if (c==' '):
                    #    output_content.append(ord('A')+0x61-1)
                    #else:
                    c2 = ord(c)
                    if (c2 > 0x40):
                        output_content.append(ord(c)+0x61)
                    else:
                        output_content.append(ord(c)+0x60)
                last_binary_ind = end+1
                #print(f"{start},{end}")
            #remaininig part
            output_content+=input_content[last_binary_ind:]
            #replacing vocabulary
            old_vocabulary_size = (output_content[0] + output_content[1]*0x100 - 2)>>1
            del output_content[:old_vocabulary_size*2+2]
            new_vocabulary = bytearray(b'\xc4\x00')
            for i in range(96):
                new_vocabulary += 0x81.to_bytes(1)
                new_vocabulary += (0x60+i).to_bytes(1)
            new_vocabulary += 0x81.to_bytes(1)
            new_vocabulary += 0x7f.to_bytes(1)
            output_content[:0] = new_vocabulary
            #saving
            new_fp = io.BytesIO(output_content)
            print(len(input_content))
            print(len(output_content))
            iso_patched.modify_file_in_place(new_fp, len(output_content), '/'+child.file_identifier().decode('utf-8'))


#patching PRO01.MES
# with iso_patched.open_file_from_iso(iso_path="/PRO01.MES;1") as input_file:
#     print(f"Patching PRO01.MES")
#     input_content = input_file.read()
#     #output_content = bytearray(input_content)
#     #first part of stream
#     output_content = bytearray(input_content[0:0x68ec])
#     #test patching vocabulary
#     for i in range(64):
#         output_content[2+i*2] = 0x81
#         output_content[2+i*2+1] = 0x80+i
#     output_content[2+64*2] = 0x81
#     output_content[2+64*2+1] = 0x7F
#     offsettt = 0x41
#     insert_str="Lorem ipsum dolor sit amet"
#     #insert_str="ABCDEFGHIJKLMOPQRSTUVWXYZ"
#     #insert_str="abcdefghijklmnopqrstuvwxyz"
#     for c in insert_str:
#         if (c==' '):
#             output_content.append(ord('A')+offsettt-1)
#         else:
#             output_content.append(ord(c)+offsettt)
#     output_content += bytearray(input_content[0x68ff:])
#     new_fp = io.BytesIO(output_content)
#     iso_patched.modify_file_in_place(new_fp, len(output_content), "/PRO01.MES;1")

#patching SIRO1A.MES

iso_patched.close()

#hard-hacking font filesize
with open(filename_iso_patched, "r+b") as iso_raw:
    iso_raw.seek(0xa5bc)
    iso_raw.write(b"\x00\x10\x00\x00\x00\x00\x10\x00")
    #print(b"\x00\x10\x00\x00\x00\x00\x10\x00")


#generate bin outta iso
with open(filename_iso_patched, 'rb') as iso_raw:
    with open(filename_iso_patched+'.bin', "wb") as bin_raw:
        with open(filename_1_bin, "rb") as bin_vanilla:
            for i in range(224903):
                buf_bin = bin_vanilla.read(2352)
                buf_iso = iso_raw.read(2048)
                buf_bin2 = buf_bin[:16]+buf_iso+buf_bin[2064:]
                bin_raw.write(buf_bin2)