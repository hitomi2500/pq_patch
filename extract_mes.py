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

def log_position(index,txt_output):
   txt_output += (bytes(f"\r\n{index:x}:",'latin1'))
   return

def log_print(text,txt_output):
   txt_output += (bytes(text,'latin1'))
   return

def fetch_cmd(index,stream,txt_output):
   log_position(index,txt_output)
   txt_output += (bytes(f"<CMD{stream[index]:x}",'latin1'))
   return index+1

def fetch_char(index,stream,txt_output):
   txt_output += (bytes(f",{stream[index]:x}",'latin1'))
   return index+1

def fetch_token(index,stream,txt_output):
   txt_output += (bytes(f"[{stream[index]:x}]",'latin1'))
   return index+1

def fetch_char_direct(index,stream,txt_output):
   txt_output += (bytes(chr(stream[index]),'latin1'))
   return index+1

def fetch_substream(index,stream,txt_output):
    i = index
    log_print('(',txt_output)
    curr_byte = stream[i]
    while (curr_byte != 3):
        #if (curr_byte > 0x40)
        if (curr_byte == 7):
            i=fetch_char(i,stream,txt_output)
            i=fetch_char(i,stream,txt_output)
            curr_byte = stream[i]
        elif (curr_byte == 8):
            i=fetch_char(i,stream,txt_output)
            i=fetch_char(i,stream,txt_output)
            i=fetch_char(i,stream,txt_output)
            curr_byte = stream[i]
        elif (curr_byte == 9):
            i=fetch_char(i,stream,txt_output)
            i=fetch_char(i,stream,txt_output)
            i=fetch_char(i,stream,txt_output)
            i=fetch_char(i,stream,txt_output)
            curr_byte = stream[i]
        else:
            log_print('TODO ',txt_output)
            i=fetch_char(i,stream,txt_output)
            curr_byte = stream[i]
    i=fetch_char(i,stream,txt_output)#fetching 3 endcode
    log_print(')',txt_output)
    return i

text_active=0
text_start_pos=0
text_data = bytearray()

def text_add(index,char):
    global text_active
    global text_data
    global text_start_pos
    if 0==text_active:
        text_active = 1
        text_start_pos = index
        text_data = bytearray()
    text_data+=char
    return

def text_end(index,txt_output,txt_output_full):
    global text_active
    global text_data
    global text_start_pos
    if 1==text_active:
        text_active = 0
        txt_output += (bytes(f"\r\n{text_start_pos:x}:{index-1:x}:",'latin1'))
        txt_output_full += (bytes(f"\r\n{text_start_pos:x}:{index-1:x}:",'latin1'))
        txt_output+=text_data
        #txt_output+='\r\n'
        txt_output_full+=text_data
        #txt_output_full+='\r\n'
    return


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
        output_content_full = bytearray()
        i = vocabulary_size*2+2
        #print(type(input_content))
        while (i<len(input_content)):
            code = input_content[i]
            if (code in {0,1,2}):
                text_end(i,output_content,output_content_full)
                code=0
                #output_content_full += (bytes(f"\r\n[{i:x}]",'latin1'))
                #output_content_full += (bytes(f"<CMD{code:x}>",'latin1'))
                #i+=1
                i=fetch_cmd(i,input_content,output_content_full)
                log_print('>',output_content_full)

            elif (code in {0x3,0x5,0x12,0x15,0x16,0x17,0x19,0x22,0x2b,0x2d,0x48,0x4c,0x4f,0x55}):
                text_end(i,output_content,output_content_full)
                i=fetch_cmd(i,input_content,output_content_full)
                log_print('>',output_content_full)

            elif (code == 4):
                text_end(i,output_content,output_content_full)
                i=fetch_cmd(i,input_content,output_content_full)
                arg1 = input_content[i]
                if (arg1 in {0x24}):
                    i=fetch_char(i,input_content,output_content_full)
                elif (arg1 in {0x18,0x19,0x1b,0x1d,0x1e,0x1f,0x23}):
                    i=fetch_char(i,input_content,output_content_full)
                else:
                    i=fetch_char(i,input_content,output_content_full)
                log_print('>',output_content_full)

            elif (code in {0xc}):
                text_end(i,output_content,output_content_full)
                i=fetch_cmd(i,input_content,output_content_full)
                i=fetch_char(i,input_content,output_content_full)
                i=fetch_substream(i,input_content,output_content_full)
                log_print('>',output_content_full)

            elif (code in {0xd}):
                text_end(i,output_content,output_content_full)
                i=fetch_cmd(i,input_content,output_content_full)
                arg1 = input_content[i]
                i=fetch_char(i,input_content,output_content_full)
                i=fetch_substream(i,input_content,output_content_full)
                if (arg1 == 0x40):
                    log_print(',type40',output_content_full)
                    i=fetch_substream(i,input_content,output_content_full)
                    while (input_content[i]==2):
                        i=fetch_char(i,input_content,output_content_full)
                        i=fetch_substream(i,input_content,output_content_full)
                else:
                    log_print(',normal',output_content_full)
                    i=fetch_substream(i,input_content,output_content_full)
                    while (input_content[i]==2):
                        i=fetch_char(i,input_content,output_content_full)
                        i=fetch_substream(i,input_content,output_content_full)
                log_print('>',output_content_full)

            elif (code in {0x7,0x8,0x9,0xa,0xb,0xf,0x11,0x13,0x18,0x1a,0x20,0x21,0x25,0x27,0x30,0x31,0x32,0x33,0x34,0x35,0x36,0x37,0x38,0x39,0x3a,0x3b,0x3c,0x3d,0x3e,0x3f,0x40,0x41,0x42,0x44,0x46,0x49,0x4a,0x4b,0x4d,0x4e,0x52,0x53,0x54,0x56,0x58,0x59,0x5a}):
                text_end(i,output_content,output_content_full)
                i=fetch_cmd(i,input_content,output_content_full)
                #output_content_full += (bytes(f"\r\n[{i:x}]",'latin1'))
                #output_content_full += (bytes(f"<CMD{code:x}",'latin1'))
                while (input_content[i]!=3):
                    i=fetch_char(i,input_content,output_content_full)
                    #i+=1
                    #output_content_full += (bytes(f",{input_content[i]:x}",'latin1'))
                #output_content_full += (bytes(f">",'latin1'))
                log_print('>',output_content_full)

            elif (code == 6):
                text_end(i,output_content,output_content_full)
                log_position(i,output_content_full)
                log_print('(FILE ',output_content_full)
                i+=1
                while (input_content[i] != 6):
                    i=fetch_char_direct(i,input_content,output_content_full)
                    #print(input_content[i])
                    #log_print(f"{i:x}",output_content_full)
                i+=1
                log_print(')',output_content_full)
                
            elif (code < 97):
                text_end(i,output_content,output_content_full)
                i=fetch_token(i,input_content,output_content)
                i=fetch_token(i,input_content,output_content_full)
                #output_content += (bytes(f"<{code:x}>",'latin1'))
                #output_content_full += (bytes(f"<{code:x}>",'latin1'))
                #code-=1
                #i+=1
            elif (code < 128):
#                if (0==text_active):
                    #log_position(i,output_content)
                    #log_position(i,output_content_full)
#                   text_start(i)
#                text_active=1
                #output_content += (code+0x20).to_bytes(1)
                #output_content_full += (code+0x20).to_bytes(1)
                text_add(i,(code+0x20).to_bytes(1))
                i+=1
                code = input_content[i]
                #output_content += code.to_bytes(1)
                #output_content_full += code.to_bytes(1)
                text_add(i,code.to_bytes(1))
                i+=1
            else:
                #if (0==text_active):
                    #log_position(i,output_content)
                    #log_position(i,output_content_full)
 #               text_active=1
                code -= 128
                assert(code >=0)
                assert(code <=127)
                text_add(i,vocabulary[code])
                #output_content += vocabulary[code]
                #output_content_full += vocabulary[code]
                i+=1

        # #saving data
        with open(output_folder + '/' + file_name + '.sjis.txt', "wb") as file:
            file.write(output_content)
        with open(output_folder + '/' + file_name + '.FULL.sjis.txt', "wb") as file:
            file.write(output_content_full)