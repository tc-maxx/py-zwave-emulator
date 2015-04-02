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

class SwitchAllCmd(EnumNamed):
	Set	   = 0x01
	Get	   = 0x02
	Report  = 0x03
	On       = 0x04
	Off      = 0x05

c_switchAllStateName = [
    "Disabled",
    "Off Enabled",
    "On Enabled",
    "On and Off Enabled"
    ]
    
class SwitchAll(CommandClass):
    
    StaticGetCommandClassId = 0x27
    StaticGetCommandClassName = "COMMAND_CLASS_SWITCH_ALL"
    
    def __init__(self, node,  data):
        CommandClass.__init__(self, node, data)
    
    GetCommandClassId = property(lambda self: self.StaticGetCommandClassId)
    GetCommandClassName = property(lambda self: self.StaticGetCommandClassName)
    reportCmd = property(lambda self: SwitchAllCmd.Report)
    getCmd = property(lambda self: SwitchAllCmd.Get)

    def getFullNameCmd(self,  _id):
        return SwitchAllCmd().getFullName(_id)

    def getDataMsg(self, _data, instance=1, multiInstanceData = []):
        msgData = []
        print 'getDataMsg {0}, multiInstanceData : {1}'.format(_data,  multiInstanceData)
        value = self._node.getValue(self.GetCommandClassId, instance, 0)
        if _data[0] == SwitchAllCmd.Get :
            msgData.append(self.GetCommandClassId)
            msgData.append(SwitchAllCmd.Report)
            msgData.append(value.getValueByte())
        return msgData
        
    def ProcessMsg(self, _data, instance=1, multiInstanceData = []):
        if _data[0] == SwitchAllCmd.Get:
            msg = Msg("SwitchAllCmd_Report", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER, False)
            value = self._node.getValue(self.GetCommandClassId, instance, 0) #  index is allways 0
            if value is not None :
                msg.Append(TRANSMIT_COMPLETE_OK)
                msg.Append(self.nodeId)
                msg.Append(3)
                msg.Append(self.GetCommandClassId)
                msg.Append(SwitchAllCmd.Report)
                msg.Append(value.getValueByte())
                self.GetDriver.SendMsg(msg, MsgQueue.NoOp)    
            else :
                msg.Append(TRANSMIT_COMPLETE_NOROUTE)
                msg.Append(self.nodeId)
                self.GetDriver.SendMsg(msg, MsgQueue.NoOp)
        elif _data[0] in [SwitchAllCmd.On, SwitchAllCmd.Off] :
            #TODO: Call manager to send at all nodes
            self._log.write(LogLevel.Warning, self, "SwitchALL on/off cmd received, Not impletmented, TODO......")
            msg = Msg("SwitchAllCmd_On-Off_Report", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER, False)
            value = self._node.getValue(self.GetCommandClassId, instance, 0) #  index is allways 0
            if value is not None :
                msg.Append(TRANSMIT_COMPLETE_OK)
                msg.Append(self.nodeId)
                msg.Append(3)
                msg.Append(self.GetCommandClassId)
                msg.Append(SwitchAllCmd.Report)
                msg.Append(value.getValueByte())
                state = value.getValueByte()
                if state == 0: # Disabled
                    self._log.write(LogLevel.Detail, self._node, "SwitchALL on/off Disabled")
                elif _data[0] == SwitchAllCmd.Off: 
                    if state == 1 or state == 255 : # Off Enabled
                        self._log.write(LogLevel.Detail, self._node, "SwitchALL Off Enabled, TODO: Simulate....")
                    else : self._log.write(LogLevel.Detail, self._node, "SwitchALL Off Disabled")
                elif _data[0] == SwitchAllCmd.On:
                    if state == 2 or state == 255 : # On Enabled
                        self._log.write(LogLevel.Detail, self._node, "SwitchALL On Enabled, TODO: Simulate....")
                    else : self._log.write(LogLevel.Detail, self._node, "SwitchALL On Disabled")
                self.GetDriver.SendMsg(msg, MsgQueue.NoOp)    
            else :
                msg.Append(TRANSMIT_COMPLETE_NOROUTE)
                msg.Append(self.nodeId)
                self.GetDriver.SendMsg(msg, MsgQueue.NoOp)

        else:
            self._log.write(LogLevel.Warning, self, "CommandClass REQUEST {0}, Not implemented : {1}".format(self.getFullNameCmd(_data[0]), GetDataAsHex(_data)))