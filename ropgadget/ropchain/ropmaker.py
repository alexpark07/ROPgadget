#!/usr/bin/env python2
## -*- coding: utf-8 -*-
##
##  Jonathan Salwan - 2014-05-13
## 
##  http://shell-storm.org
##  http://twitter.com/JonathanSalwan
## 
##  This program is free software: you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software  Foundation, either  version 3 of  the License, or
##  (at your option) any later version.
##

from capstone           import *
from arch.ropmakerx86   import *
from arch.ropmakerx64   import *
from arch.ropmakerthumb import *

class ROPMaker:
    def __init__(self, binary, gadgets, offset, isThumb=False):
        self.__binary  = binary
        self.__gadgets = gadgets
        self.__offset  = offset
        self.__isThumb = isThumb

        self.__handlerArch()

    def __handlerArch(self):

        if self.__binary.getArch() == CS_ARCH_X86           \
            and self.__binary.getArchMode() == CS_MODE_32   \
            and self.__binary.getFormat() == "ELF":
            ROPMakerX86(self.__binary, self.__gadgets, self.__offset)

        elif self.__binary.getArch() == CS_ARCH_X86         \
            and self.__binary.getArchMode() == CS_MODE_64   \
            and self.__binary.getFormat() == "ELF":
            ROPMakerX64(self.__binary, self.__gadgets, self.__offset)

        # Thumb Mode Only
        elif self.__binary.getArch() == CS_ARCH_ARM          \
            and self.__binary.getArchMode() == CS_MODE_32    \
            and self.__binary.getFormat() == "ELF":
            if self.__isThumb == True:
                ROPMakerTHUMB(self.__binary, self.__gadgets, self.__offset)

        else:
            print "\n[Error] ROPMaker.__handlerArch - Arch not supported yet for the rop chain generation"

