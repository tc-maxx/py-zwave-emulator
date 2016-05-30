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
from lib.values import ValueType

class ConfigurationCmd(EnumNamed):
	Set	= 0x04
	Get	= 0x05
	Report	= 0x06

class Configuration(CommandClass):
    
    StaticGetCommandClassId = 0x70
    StaticGetCommandClassName = "COMMAND_CLASS_CONFIGURATION"
    
    def __init__(self, node,  data):
        CommandClass.__init__(self, node, data)
    
    GetCommandClassId = property(lambda self: self.StaticGetCommandClassId)
    GetCommandClassName = property(lambda self: self.StaticGetCommandClassName)

    def getFullNameCmd(self,  _id):
        return ConfigurationCmd().getFullName(_id)

    def ProcessMsg(self, _data, instance=1, multiInstanceData = []):
        if _data[0] == ConfigurationCmd.Get:
            msg = Msg("ConfigurationCmd_Report", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER)
            param = _data[1]
            value = self._node.getValue(self.GetCommandClassId, instance, param)
            if value is not None :
                msg.Append(TRANSMIT_COMPLETE_OK)
                msg.Append(self.nodeId)
                val = value.getValueHex()
                if val is None :
                    self._log.write(LogLevel.Error, self, "Invalid type ({0}) for configuration parameter {1}".format(value.type, param))
                    return
                msg.Append(3 + len(val))
                msg.Append(self.GetCommandClassId)
                msg.Append(ConfigurationCmd.Report)
                msg.Append(param)
                for v in val: msg.Append(v)
                self.GetDriver.SendMsg(msg, MsgQueue.NoOp)    
            else :
                msg.Append(TRANSMIT_COMPLETE_NOROUTE)
                msg.Append(self.nodeId)
                self.GetDriver.SendMsg(msg, MsgQueue.NoOp)

        else:
            self._log.write(LogLevel.Warning, self, "CommandClass REQUEST {0}, Not implemented : {1}".format(self.getFullNameCmd(_data[0]), GetDataAsHex(_data)))

