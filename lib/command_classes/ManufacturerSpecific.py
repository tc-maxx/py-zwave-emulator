# -*- coding: utf-8 -*-

"""
.. module:: libopenzwave

This file is part of **python-openzwave-emulator** project http:#github.com/p/python-openzwave-emulator.
    :platform: Unix, Windows, MacOS X
    :sinopsis: openzwave simulator Python

This project is based on python-openzwave to pass thought hardware zwace device. It use for API developping or testing.
All C++ and cython code are moved.

.. moduleauthor: Nico0084 <nico84dev@gmail.com>
.. moduleauthor: bibi21000 aka Sébastien GALLET <bibi21000@gmail.com>
.. moduleauthor: Maarten Damen <m.damen@gmail.com>

License : GPL(v3)

**python-openzwave** is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

**python-openzwave** is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with python-openzwave. If not, see http:#www.gnu.org/licenses.

"""

from zwemulator.lib.defs import *
from zwemulator.lib.log import LogLevel
from zwemulator.lib.driver import MsgQueue, Msg
from commandclass import CommandClass

class ManufacturerSpecificCmd(EnumNamed):
	Get		= 0x04
	Report	= 0x05

class ManufacturerSpecific(CommandClass):
    
    StaticGetCommandClassId = 0x72
    StaticGetCommandClassName = "COMMAND_CLASS_MANUFACTURER_SPECIFIC"
    
    def __init__(self, node,  data):
        CommandClass.__init__(self, node, data)
    
    GetCommandClassId = property(lambda self: self.StaticGetCommandClassId)
    GetCommandClassName = property(lambda self: self.StaticGetCommandClassName)

    def getFullNameCmd(self,  _id):
        return ManufacturerSpecificCmd().getFullName(_id)
        
    def ProcessMsg(self, _data, instance=1):
        msg = Msg( "ManufacturerSpecificCmd_Report", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER, False)
        if _data[0] == ManufacturerSpecificCmd.Get:
            msg.Append(TRANSMIT_COMPLETE_OK)
            msg.Append(self.nodeId)
            msg.Append(0x08)
            msg.Append(self.GetCommandClassId)
            msg.Append(ManufacturerSpecificCmd.Report)
            # first two bytes are manufacturer id code
            manufacturerId = int(self._node.GetManufacturerId, 16)
            msg.Append((manufacturerId & 0x0000ff00)>>8)
            msg.Append((manufacturerId & 0x000000ff))
            # next four are product type and product id
            productType = int(self._node.GetProductType,  16)
            msg.Append((productType & 0x0000ff00)>>8)
            msg.Append((productType & 0x000000ff))
            productId = int(self._node.GetProductId, 16)
            msg.Append((productId & 0x0000ff00)>>8)
            msg.Append((productId & 0x000000ff))
            self.GetDriver.SendMsg(msg, MsgQueue.NoOp)