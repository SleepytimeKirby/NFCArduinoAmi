#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os,sys,random
import PyCmdMessenger

try: 
    bin_file = sys.argv[1]
except:
    print("\nUsage: %s /path/to/amiibo.bin\n" % sys.argv[0])
    raise SystemExit(0)
arduino = PyCmdMessenger.ArduinoBoard("COM3",baud_rate=9600,timeout=30.0)
commands = [["kSendNFCUID",""],
            ["kReciveNFCUID","bbbbbbb"],
            ["kWriteBinNFC",""],
            ["kWriteLocksNFC",""],
            ["kSendMessage","?"],
            ["kFillData","ib"],
            ]
c = PyCmdMessenger.CmdMessenger(arduino,commands)
c.send("kSendNFCUID")
msg = c.receive()
uid0 = msg[1][0]
uid1 = msg[1][1]
uid2 = msg[1][2]
bcc0 = uid0 ^ uid1 ^ uid2 ^ ord('\x88')
uid3 = msg[1][3]
uid4 = msg[1][4]
uid5 = msg[1][5]
uid6 = msg[1][6]
bcc1 = uid3 ^ uid4 ^ uid5 ^uid6
pwd1 = ord('\xAA') ^ uid1 ^ uid3
pwd2 = ord('\x55') ^ uid2 ^ uid4
pwd3 = ord('\xAA') ^ uid3 ^ uid5
pwd4 = ord('\x55') ^ uid4 ^ uid6

print("Using new serial: %02X%02X%02X%02X%02X%02X%02X%02X%02X" % (uid0, uid1, uid2, bcc0, uid3, uid4, uid5, uid6, bcc1))
print("\nDecrypting %s\n" % bin_file)

#decrypting to decrypt.bin
print("amiitool.exe -d -k key_retail.bin -i '" + bin_file + "' -o decrypt.bin\n")
os.system("amiitool.exe -d -k key_retail.bin -i '" + bin_file + "' -o decrypt.bin")

try:
    with open('decrypt.bin', 'r+b') as fh:
        print("File decrypted\n")
        print("Injecting new serial\n")
        fh.seek(0, 0)
        fh.write(bytes([bcc1]))
        fh.seek(0x1D4, 0)
        fh.write(bytes([uid0, uid1, uid2, bcc0, uid3, uid4, uid5, uid6]))
        fh.seek(0x214,0)
        fh.write(bytes([pwd1, pwd2, pwd3, pwd4, ord('\x80'),ord('\x80')]))
        fh.close()
except:
    print('\nAborting!\n')
    raise SystemExit(0)

print("Encrypting file\n")
print("amiitool.exe -e -k key_retail.bin -i decrypt.bin -o encrypt.bin")
os.system("amiitool.exe -e -k key_retail.bin -i decrypt.bin -o encrypt.bin")
print("Cleaning up...")
#os.system("del decrypt.bin")
try:
    with open('encrypt.bin', 'rb') as fh:
        print("Opening encrypted file for transfer\n")
        print("transfering")
        i = 0
        while True:
            chunk = fh.read(1)
            if chunk == b'':
                break
            c.send("kFillData",i,ord(chunk))
            c.receive();
            i += 1
        fh.close()
except:
    print('\nAborting!\n')
    raise SystemExit(0)
print("Operation Complete\n\n")  
c.send("kWriteBinNFC")
print("Start Write.") 
msg = c.receive()
print("Write Complete.") 
if(msg[1]):
    c.send("kWriteLocksNFC")
    msg = c.receive()
    if(msg[1]):
        print("Lock Complete! All Done")
    else:
        print("Error writting lock! Please try again.")
else:
    print("Error Writting Data! Please try again.")
SystemExit(0)