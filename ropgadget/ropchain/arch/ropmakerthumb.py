#!/usr/bin/env python2
## -*- coding: utf-8 -*-
##  
##  Project owner: Jonathan Salwan
##  
##  Coded by alex.park
##
##  This program is free software: you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software  Foundation, either  version 3 of  the License, or
##  (at your option) any later version.
##

import re
from   capstone import *

class REGS:
    r0  = False
    r1  = False
    r2  = False
    r3  = False
    r4  = False
    r5  = False
    r6  = False
    r7  = False
    r8  = False
    r9  = False
    r10 = False
    r11 = False
    r12 = False
    sp  = False
    lr  = False
    pc  = False
    enable_regs = []
    enable_count = 0

class ROPMakerTHUMB:
    def __init__(self, binary, gadgets, liboffset=0x0):
        self.__binary  = binary
        self.__gadgets = gadgets

        # If it's a library, we have the option to add an offset to the addresses
        self.__liboffset = liboffset

        self.__generate()

    def __lookingForPopPc(self, gadgetsAlreadyTested):
        POP_PC = []
        for gadget in self.__gadgets:
            if gadget in gadgetsAlreadyTested:
                continue
            f = gadget["gadget"].split(" ; ")[0]
            # regex -> pop {r0,..., pc}
            #regex = re.search("pop {r0,.*?, pc}$", f)
            regex = re.search("pop {.*?, pc}$", f)
            if regex:
                lg = gadget["gadget"].split(" ; ")[0]
                if lg:
                    regex = re.findall("{(.*?)}", lg)
                    if len(regex) > 0:
                        rv = regex[0].split(', ')
                    else:
                        # there is no result in regex
                        continue
                try:
                    R = {}
                    idx = 0
                    for r in rv:
                        R[idx] = r
                        idx = idx + 1

                    print "\t[+] Gadget found: 0x%x %s" %(gadget["vaddr"], gadget["gadget"])
                    POP_PC.append(R)
                except:
                    continue


        if len(POP_PC) == 0: return None
        else: return POP_PC

    def __padding(self, gadget, regAlreadSetted):
        lg = gadget["gadget"].split(" ; ")
        for g in lg[1:]:
            if g.split()[0] == "pop":
                reg = g.split()[1]
                try:
                    print "\tp += pack('<I', 0x%08x) # padding without overwrite %s" %(regAlreadSetted[reg], reg)
                except KeyError:
                    print "\tp += pack('<I', 0x41414141) # padding"

    def __buildRopChain(self, POP_R0_PC):

        sects = self.__binary.getDataSections()
        #print dir(self.__binary)
        dataAddr = None
        for s in sects:
            if s["name"] == ".data":
                dataAddr = s["vaddr"] + self.__liboffset
        if dataAddr == None:
            print "\n[-] Error - Can't find a writable section"
            return

        print "\t#!/usr/bin/env python2"
        print "\t# execve generated by ROPgadget\n" 
        print "\tfrom struct import pack\n"

        print "\t# Padding goes here"
        print "\tp = ''\n"

    def __generate(self):

        # To find the smaller gadget
        self.__gadgets.reverse()

        print "\nROP chain generation\n==========================================================="

        print "\n- Step 1 -- Pop Rx and PC gadgets\n"

        gadgetsAlreadyTested = []
        while True:
            POP_PC = self.__lookingForPopPc(gadgetsAlreadyTested)

            if not POP_PC:
                print "\t[-] Can't find the 'pop {r0, ..., pc}' gadget"
                return

            else:
                break

        print "\n- Step 5 -- Build the ROP chain\n"

        self.__buildRopChain(POP_PC)

