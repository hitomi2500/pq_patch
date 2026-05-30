from pathlib import Path
import os
import sys

SECTOR_SIZE = 2352

directory_path = Path('D:\\Saturn\\PrincessQuest\\ISO')
filename_track1 = 'Princess Quest (Japan) (Track 1).bin'   
filename_track2 = 'Princess Quest (Japan) (Track 2).bin'   

os.chdir(directory_path)

if not os.path.exists(filename_track1):
    print(f"Cannot find file : {filename_track1}\n")
    sys.exit(0)

if not os.path.exists(filename_track2):
    print(f"Cannot find file : {filename_track2}\n")
    sys.exit(0)

with open(filename_track1, mode='rb') as track1_file:
    with open(filename_track2, mode='rb') as track2_file:
        with open(filename_track1.replace(' (Track 1).bin','.iso'), mode='wb') as iso_file:
            #track 1
            while True:
                chunk = track1_file.read(SECTOR_SIZE)
                if not chunk:
                    break
                iso_file.write(chunk[16:16+2048])
            #gap
            zero_array = bytearray(2048)
            for i in range (2*75):
                iso_file.write(zero_array)
            #track 2
            while True:
                chunk = track2_file.read(SECTOR_SIZE)
                if not chunk:
                    break
                iso_file.write(chunk[16:16+2048])
