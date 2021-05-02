# pip install pyinstaller
# Windows Freeze: Run > cmd > pyinstaller --onefile --noconsole PyTOD2.py

from tkinter import *
import tkinter.messagebox as box

import sys
import os
import re
import json
import struct
import subprocess
import shutil
import string

#Prevents PC becoming hostage
from subprocess import CREATE_NO_WINDOW

#Copy SLPS file and rename to new_SLPS
from shutil import copyfile


low_bits = 0x3F
high_bits = 0xFFFFFFC0
pointer_begin = 0xDD320
pointer_end = 0xE62EF

tags = {0x4: 'color', 0x5: 'size', 0x6: 'num', 0x7: 'char', 0x8: 'item', 0x9: 'button'}
names = {1: 'Kyle', 2: 'Reala', 3: 'Loni', 4: 'Judas', 5: 'Nanaly', 6: 'Harold' }

com_tag = r'(<\w+:?\w+>)'
hex_tag = r'(\{[0-9A-F]{2}\})'

printable = ''.join((string.digits,string.ascii_letters,string.punctuation,' '))

def get_pointers():
    f = open('SLPS_251.72', 'rb')
    f.seek(pointer_begin, 0)
    pointers = []

    while f.tell() < pointer_end:
        p = struct.unpack('<L', f.read(4))[0]
        pointers.append(p)

    f.close()
    return pointers

def mkdir(name):
    try: os.mkdir(name)
    except: pass

def compress_comptoe(name, ctype=1):
    c = '-c%d' % ctype
    subprocess.run(['comptoe.exe', c, name, name + '.c'], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW)

def decompress_comptoe(name):
    subprocess.run(['comptoe.exe', '-d', name, name + '.d'], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW)

# by flame1234
def decode(param):
    a2 = param
    a3 = 0x993F
    a1 = 0x9940
    if  a3 >= a2:
        a2 = a1
    a1 = a2 >> 8
    a0 = a2 & 0xFF
    t0 = True if a1 < 0xE0 else False
    v1 = a1 - 0x40
    a3 = a0 - 1
    a2 = True if a0 < 0x80 else False
    if t0 == False:
        a1 = v1 & 0xFFFF
    t1 = a1 - 0x99
    t0 = t1 & 0xFFFF
    v0 = 0xBB
    a1 = t0 * v0
    if a2 == False:
        a0 = a3 & 0xFFFF
    t2 = True if a0 < 0x5D else False
    v1 = a0 - 1
    if t2 == False:
        a0 = v1 & 0xFFFF
    t5 = a0 - 0x40
    t4 = t5 & 0xFFFF
    t3 = a1 + t4
    v0 = t3 & 0xFFFF

    return v0

def extract_fpb():
    f = open('FILE.FPB', 'rb')
    json_file = open('FPB.json', 'r')
    json_data = json.load(json_file)
    #ext_file = open('TREE.json', 'r')
    #ext_data = json.load(ext_file)
    #ext_file.close()
    pointers = get_pointers()
    mkdir('FPB')
    
    for i in range(len(pointers) - 1):
        remainder = pointers[i] & low_bits
        start = pointers[i] & high_bits
        end = (pointers[i+1] & high_bits) - remainder
        size = end - start
        if size == 0:
            #json_data[i] = 'dummy'
            continue
        f.seek(start, 0)
        data = f.read(size)
        extension = json_data['%05d' %i]
        #if ('%05d' % i) in ext_data.keys():
        #    extension = ext_data['%05d' % i]
        #json_data['%05d' % i] = extension
        o = open('FPB/' + '%05d.%s' % (i, extension), 'wb')
        o.write(data)
        o.close()

    #json.dump(json_data, json_file, indent = 4)
    f.close()

def extract_scpk():
    mkdir('SCPK')
    json_file = open('SCPK.json', 'w')
    json_data = {}
    
    for file in os.listdir('FPB'):
        if not file.endswith('scpk'):
            continue
        f = open('FPB/%s' % file, 'rb')
        header = f.read(4)
        if header != b'SCPK':
            f.close()
            continue
        mkdir('SCPK/%s' % file.split('.')[0])
        index = file.split('.')[0]
        json_data[index] = {}
        f.read(4)
        files = struct.unpack('<L', f.read(4))[0]
        f.read(4)
        sizes = []
        for i in range(files):
            sizes.append(struct.unpack('<L', f.read(4))[0])
        for i in range(files):
            ext = 'bin'
            if i == files - 1:
                ext = 'sced'
            fname = 'SCPK/%s/%02d.%s' % (file.split('.')[0], i, ext)
            o = open(fname, 'wb')
            data = f.read(sizes[i])
            json_data[index][i] = data[0]
            o.write(data)
            o.close()
            if i == files - 1:
                if data[0] == 1 or data[0] == 3:
                    decompress_comptoe(fname)
                    os.remove(fname)
                    os.rename(fname + '.d', fname)

        f.close()
        
    json.dump(json_data, json_file, indent = 4)

def move_sced():
    mkdir('SCED')
    sced_dir = os.getcwd() + '/SCED/'
    
    for folder in os.listdir('SCPK'):
        if not os.path.isdir('SCPK/' + folder):
            continue
        f = sorted(os.listdir('SCPK/' + folder))[-1]
        new_name = '%s_%s.sced' % (folder, f.split('.')[0])
        shutil.copy(os.path.join('SCPK', folder, f), sced_dir + new_name)

def extract_sced():
    move_sced()
    mkdir('TXT')
    mkdir('TXT_EN')
    json_file = open('TBL.json', 'r')
    #json_file2 = open('TBL2.json', 'w')
    json_data = json.load(json_file)
    json_file.close()
    sced_file = open('SCED.json', 'w')
    sced_data = {}
    #sced_file = open('sced.json', 'r')
    #sced_data = json.load(sced_file)
    #sced_file.close()
    
    #char_file = open('00019.bin', 'r', encoding='cp932')
    #char_index = char_file.read()
    #char_file.close()

    for name in os.listdir('SCED/'):
        f = open('SCED/' + name, 'rb')
        header = f.read(4)
        if header != b'\x53\x43\x45\x44':
            continue
        o = open('TXT/' + name + '.txt', 'w', encoding = 'utf-8')
        sced_data[name] = []
        pointer_block = struct.unpack('<L', f.read(4))[0]
        text_block = struct.unpack('<L', f.read(4))[0]
        fsize = os.path.getsize('SCED/' + name)
        text_pointers = []
        addrs = []
        f.seek(pointer_block, 0)
        
        while f.tell() < text_block:
            b = f.read(1)
            if b == b'\xF8':
                addr = struct.unpack('<H', f.read(2))[0]
                #if f.tell() - 2 in sced_data[name]:
                if (addr < fsize - text_block) and (addr > 0):
                    addrs.append(f.tell() - 2)
                    text_pointers.append(addr)

        for i in range(len(text_pointers)):
            f.seek(text_block + text_pointers[i] - 1, 0)
            b = f.read(1)
            if b != b'\x00':
                continue
            sced_data[name].append(addrs[i])
            b = f.read(1)
            while b != b'\x00':
                b = ord(b)
                if (b >= 0x99 and b <= 0x9F) or (b >= 0xE0 and b <= 0xE4):
                    c = (b << 8) + ord(f.read(1))
                    #if str(c) not in json_data.keys():
                    #    json_data[str(c)] = char_index[decode(c)]
                    o.write(json_data[str(c)])
                elif b == 0x1:
                    o.write('\n')
                elif b in (0x3, 0x4, 0x5, 0x6, 0x7, 0x8, 0x9, 0xB):
                    b2 = struct.unpack('<L', f.read(4))[0]
                    if b in tags:
                        if b == 0x7 and b2 in names:
                            o.write('<%s>' % names[b2])
                        else:
                            o.write('<%s:%08X>' % (tags[b], b2))
                    else:
                        o.write('<%02X:%08X>' % (b, b2))
                elif chr(b) in printable:
                    o.write(chr(b))
                elif b >= 0xA1 and b < 0xE0:
                    o.write(struct.pack('B', b).decode('cp932'))
                elif b in (0x12, 0x14, 0x15, 0x16, 0x17, 0x18):
                    o.write('{%02X}' % b)
                    next_b = b''
                    while next_b not in (b'\xBC', b'\xC0'):
                        next_b = f.read(1)
                        o.write('{%02X}' % ord(next_b))
                else:
                    o.write('{%02X}' % b)
                b = f.read(1)
            o.write('\n-----------------------\n')
        f.close()
        o.close()
        
    #json.dump(json_data, json_file2, indent=4)
    json.dump(sced_data, sced_file, indent=4)

def insert_sced():
    json_file = open('TBL.json', 'r')
    sced_json = open('SCED.json', 'r')
    table = json.load(json_file)
    sced_data = json.load(sced_json)
    json_file.close()
    sced_json.close()
    
    itable = dict([[i,struct.pack('>H', int(j))] for j,i in table.items()])
    itags = dict([[i,j] for j,i in tags.items()])
    inames = dict([[i,j] for j,i in names.items()])
    
    mkdir('SCED_NEW/')

    for name in os.listdir('txt_en'):
        f = open('txt_en/' + name, 'r', encoding='utf8')
        name = name[:-4]
        sced = open('sced/' + name, 'rb')
        o = open('sced_new/' + name, 'wb')

        txts = []
        sizes = []
        txt = bytearray()

        for line in f:
            line = line.strip('\x0A')
            if len(line) > 0:
                if line[0] == '#':
                    continue
            if '-----------------------' in line:
                txts.append(txt[:-1] + b'\x00')
                sizes.append(len(txt))
                txt = bytearray()
            else:
                string_hex = re.split(hex_tag, line)
                string_hex = [sh for sh in string_hex if sh]
                for s in string_hex:
                    if re.match(hex_tag, s):
                        txt += (struct.pack('B', int(s[1:3], 16)))
                    else:
                        s_com = re.split(com_tag, s)
                        s_com = [sc for sc in s_com if sc]
                        for c in s_com:
                            if re.match(com_tag, c):
                                if ':' in c:
                                    split = c.split(':') 
                                    if split[0][1:] in itags.keys():
                                        txt += (struct.pack('B', itags[split[0][1:]]))
                                    else:
                                        txt += (struct.pack('B', int(split[0][1:], 16)))
                                    txt += (struct.pack('<I', int(split[1][:8], 16)))
                                else:
                                    txt += struct.pack('B', 0x7)
                                    txt += struct.pack('<I', inames[c[1:-1]])
                                    
                            else:
                                for c2 in c:
                                    if c2 in itable.keys():
                                        txt += itable[c2]
                                    else:
                                        txt += c2.encode('cp932')
                txt += (b'\x01')
                
        f.close()
        
        sced.seek(8, 0)
        pointer_block = struct.unpack('<L', sced.read(4))[0]
        sced.seek(0, 0)
        header = sced.read(pointer_block)
        o.write(header + b'\x00')
        sced.close()

        pos = 1
        for i in range(len(txts)):
            o.seek(sced_data[name][i], 0)
            o.write(struct.pack('<H', pos))
            pos += sizes[i]

        o.seek(pointer_block + 1, 0)
        
        for t in txts:
            o.write(t)
            
        o.close()

def pack_scpk():
    mkdir('SCPK_PACKED')
    json_file = open('SCPK.json', 'r')
    json_data = json.load(json_file)
    json_file.close()

    for name in os.listdir('sced_new'):
        folder = name[:5]
        if not os.path.isdir('scpk/' + folder):
            continue
        if os.path.isdir('scpk/' + folder):
            sizes = []
            o = open('scpk_packed/%s.SCPK' % folder, 'wb')
            data = bytearray()
            listdir = os.listdir('scpk/' + folder)
            for file in listdir:
                read = bytearray()
                index = str(int(file.split('.')[0]))
                fname = 'scpk/%s/%s' % (folder, file)
                f = open(fname, 'rb')
                ctype = json_data[folder][index]
                if file == listdir[-1]:
                    if ctype != 0:
                        fname = 'sced_new/' + name
                        compress_comptoe(fname, ctype)
                        comp = open(fname + '.c', 'rb')
                        read = comp.read()
                        comp.close()
                        os.remove(fname + '.c')
                    else:
                        read = f.read()
                else:
                    read = f.read()
                data += read
                sizes.append(len(read))
                f.close()
                
            o.write(b'\x53\x43\x50\x4B\x01\x00\x07\x00')
            o.write(struct.pack('<L', len(sizes)))
            o.write(b'\x00' * 4)
            
            for i in range(len(sizes)):
                o.write(struct.pack('<L', sizes[i]))
                
            o.write(data)
            o.close()

def move_scpk_packed():
    for f in os.listdir('SCPK_PACKED'):
        shutil.copy(os.path.join('SCPK_PACKED', f), 'FPB/' + f)

def pack_fpb():
    move_scpk_packed()
    sectors = [0]
    remainders = []
    buffer = 0
    json_file = open('FPB.json', 'r')
    json_data = json.load(json_file)
    json_file.close()
    #ext_file = open('tree.json', 'r')
    #ext_data = json.load(ext_file)
    #ext_file.close()
    o = open('FILE_NEW.FPB', 'wb')

    #print ("Packing FPB...")
    
    for k, v in json_data.items():
        size = 0
        remainder = 0
        if v != 'dummy':
            f = open('fpb/%s.%s' % (k, v), 'rb')
            o.write(f.read())
            size = os.path.getsize('fpb/%s.%s' % (k, v))
            remainder = 0x40 - (size % 0x40)
            if remainder == 0x40:
                remainder = 0
            o.write(b'\x00' * remainder)
            f.close()
        remainders.append(remainder)
        buffer += (size + remainder)
        sectors.append(buffer)

    copyfile('SLPS_251.72', 'new_SLPS_251.72')
    u = open('new_SLPS_251.72', 'r+b')
    u.seek(pointer_begin)
    
    for i in range(len(sectors) - 1):
        u.write(struct.pack('<L', sectors[i] + remainders[i]))
        
    o.close()
    u.close()

'''
Graphical Interface Start
'''

window = Tk()

window.title("PyTOD2 - Tales of Destiny 2 (PS2) Tool")

#Set working directory for GUI
os.chdir('C:/Users/pvnn/Desktop')

label = Label(window, text = "PyTOD2 unpacks resources from Tales of Destiny 2 (PS2) and repacks them.")
#label.pack(padx = 200, pady = 50)
label.pack(anchor="w")


cwd = Label(window, text = "Current Working Directory: " + os.getcwd())
cwd.pack(anchor="w")
#path_SLPS = Label(window, text = "Path to SLPS_251.72")
#path_SLPS.pack(anchor="w")

btn_unpackFPB = Button(text="Unpack FPB", command = extract_fpb)
btn_unpackFPB.pack(side=LEFT)

btn_unpackSCPK = Button(text="Unpack SCPK", command = extract_scpk)
btn_unpackSCPK.pack(side=LEFT)

btn_unpackSCED = Button(text="Unpack SCED", command = extract_sced)
btn_unpackSCED.pack(side=LEFT)

btn_unpackSCED = Button(text="Pack SCED", command = insert_sced)
btn_unpackSCED.pack(side=RIGHT)

btn_unpackSCPK = Button(text="Pack SCPK", command = pack_scpk)
btn_unpackSCPK.pack(side=RIGHT)

btn_unpackFPB = Button(text="Pack FPB", command = pack_fpb)
btn_unpackFPB.pack(side=RIGHT)




window.mainloop()



'''
def tog():
    if window.cget("bg") == "black":
        window.configure(bg="gray")
    else:
        window.configure(bg="black")

btn_tog = Button(window, text="Dark Mode", command=tog)
btn_tog.pack(padx = 200, pady = 10)

def dialog():
    var= box.askyesno("Message Box", "Proceed?")
    if var == 1:
        box.showinfo("Yes Box", "Proceeding...")
    else:
        box.showwarning("No Box", "Cancelling...")

btn = Button(window, text="Click", command=dialog)
btn.pack(padx = 150, pady = 50)

#btn_end = Button(window, text="Close", command=exit)
#btn_end.pack(anchor="se")
    #padx = 150, pady = 20
'''




