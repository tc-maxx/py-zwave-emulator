# -*- coding: utf-8 -*-

"""
.. module:: zwemulator

This file is part of **py-zwave-emulator** project #https://github.com/Nico0084/py-zwave-emulator.
    :platform: Unix, Windows, MacOS X
    :sinopsis: ZWave emulator Python

This project is based on openzwave #https://github.com/OpenZWave/open-zwave to pass thought hardware zwave device. It use for API developping or testing.

- Openzwave config files are use to load a fake zwave network an handle virtual nodes. All configured manufacturer device cant be create in emulator.
- Use serial port emulator to create com, you can use software like socat #http://www.dest-unreach.org/socat/
- eg command line : socat -d -d PTY,ignoreeof,echo=0,raw,link=/tmp/ttyS0 PTY,ignoreeof,echo=0,raw,link=/tmp/ttyS1 &
- Run from bin/zwemulator.py
- Web UI access in local, port 4500


.. moduleauthor: Nico0084 <nico84dev@gmail.com>

License : GPL(v3)

**py-zwave-emulator** is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

**py-zwave-emulator** is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with py-zwave-emulator. If not, see http:#www.gnu.org/licenses.

"""

from lib.defs import *
from lib.log import LogLevel
from lib.driver import MsgQueue, Msg
from commandclass import CommandClass

class PowerLevelEnum:
    Normal = 0
    Minus1dB = 1
    Minus2dB = 2
    Minus3dB = 3
    Minus4dB = 4
    Minus5dB = 5
    Minus6dB = 6
    Minus7dB = 7
    Minus8dB = 8
    Minus9dB = 9

class PowerLevelStatusEnum:
    Failed = 0
    Success = 1
    InProgress = 2

class PowerlevelCmd(EnumNamed):
    Set		         = 0x01
    Get			     = 0x02
    Report			 = 0x03
    TestNodeSet	 = 0x04
    TestNodeGet	 = 0x05
    TestNodeReport = 0x06

class PowerlevelIndex:
    Powerlevel = 0
    Timeout = 1
    Set = 2
    TestNode = 3
    TestPowerlevel = 4
    TestFrames = 5
    Test = 6
    Report = 7
    TestStatus = 8
    TestAckFrames = 9

c_powerLevelNames = [
    "Normal",
    "-1dB",
    "-2dB",
    "-3dB",
    "-4dB",
    "-5dB",
    "-6dB",
    "-7dB",
    "-8dB",
    "-9dB"
    ]

c_powerLevelStatusNames = [
    "Failed",
    "Success",
    "In Progress"
    ]
    
class Powerlevel(CommandClass):
    
    StaticGetCommandClassId = 0x73
    StaticGetCommandClassName = "COMMAND_CLASS_POWERLEVEL"
    
    def __init__(self, node,  data):
        CommandClass.__init__(self, node, data)
    
    GetCommandClassId = property(lambda self: self.StaticGetCommandClassId)
    GetCommandClassName = property(lambda self: self.StaticGetCommandClassName)

    def getFullNameCmd(self,  _id):
        return PowerlevelCmd().getFullName(_id)

    def getByteIndex(self, instance):
        return PowerlevelIndex.Powerlevel

    def getDataMsg(self, _data, instance=1):
        msgData = []
        if _data[0] == PowerlevelCmd.Get:
            powerValue = self._node.getValue(self.GetCommandClassId, instance, PowerlevelIndex.Powerlevel)
            powerTimeout = self._node.getValue(self.GetCommandClassId, instance, PowerlevelIndex.Timeout)
            if powerValue is not None and powerTimeout is not None :
                msgData.append(self.GetCommandClassId)
                msgData.append(PowerlevelCmd.Report)
                msgData.append(powerValue._value)
                msgData.append(powerTimeout._value)
        return msgData        

    def ProcessMsg(self, _data, instance=1, multiInstanceData = []):
        if _data[0] == PowerlevelCmd.Get:
            msg = Msg("PowerlevelCmd_Report", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER)
            msgData = self.getDataMsg(_data, instance)
            if msgData :
                if multiInstanceData :
                    multiInstanceData[2] += len(msgData)
                    for v in multiInstanceData : msg.Append(v)
                else :
                    msg.Append(TRANSMIT_COMPLETE_OK)
                    msg.Append(self.nodeId)
                    msg.Append(len(msgData))
                for v in msgData : msg.Append(v)
                self.GetDriver.SendMsg(msg, MsgQueue.NoOp)    
            else :
                msg.Append(TRANSMIT_COMPLETE_NOROUTE)
                msg.Append(self.nodeId)
                self.GetDriver.SendMsg(msg, MsgQueue.NoOp)

        else:
            self._log.write(LogLevel.Warning, self, "CommandClass REQUEST {0}, Not implemented : {1}".format(self.getFullNameCmd(_data[0]), GetDataAsHex(_data)))
