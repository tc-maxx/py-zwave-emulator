#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
.. module:: libozwctlremulator

This file is part of **python-ozw-ctlr-emulator** project http://github.com/Nico0084/python-ozw-ctlr-emulator.
    :platform: Unix
    :sinopsis: openzwave controller serial simulator Python

This project is based on openzwave lib to pass thought hardware zwave device. It use for API developping or testing.
Based on openzwave project config files to simulate a zwave network and his nodes.
All C++ and cython code are moved.

.. moduleauthor: Nico0084 <nico84dev@gmail.com>

License : GPL(v3)

**python-ozw-ctlr-emulator** is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

**python-ozw-ctlr-emulator** is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with python-openzwave. If not, see http://www.gnu.org/licenses.

"""
from zwemulator.lib.defs import *
from zwemulator.lib.node import NodeData,  Node
from zwemulator.lib.driver import DriverData, Driver
from zwemulator.lib.driver import ControllerInterface, ControllerCommand, ControllerState #, pfnControllerCallback_t
from zwemulator.lib.notification import Notification, NotificationType, NotificationsWatcher
from zwemulator.lib.values import ValueGenre, ValueType, ValueID
from zwemulator.lib.options import Options
from zwemulator.lib.log import Log, LogLevel
from zwemulator.lib.vers import ozw_vers_major, ozw_vers_minor, ozw_vers_revision
from zwemulator.lib.xmlfiles import networkFileConfig,  DeviceClasses,  Manufacturers
from zwemulator.lib.command_classes.commandclasses import CommandClasses
import os
import re
import threading

MANAGER = None  # A Singleton for manager
OPTIONS = Options() # A Singleton for Options

#SUPPORTEDCOMMANDCLASSES = {
#    0x71: "COMMAND_CLASS_ALARM", 
#    0x22: "COMMAND_CLASS_APPLICATION_STATUS", 
#    0x85: "COMMAND_CLASS_ASSOCIATION", 
#    0x9b: "COMMAND_CLASS_ASSOCIATION_COMMAND_CONFIGURATION", 
#    0x20: "COMMAND_CLASS_BASIC", 
#    0x50: "COMMAND_CLASS_BASIC_WINDOW_COVERING", 
#    0x80: "COMMAND_CLASS_BATTERY", 
#    0x46: "COMMAND_CLASS_CLIMATE_CONTROL_SCHEDULE", 
#    0x81: "COMMAND_CLASS_CLOCK", 
#    0x70: "COMMAND_CLASS_CONFIGURATION", 
#    0x21: "COMMAND_CLASS_CONTROLLER_REPLICATION", 
#    0x56: "COMMAND_CLASS_CRC_16_ENCAP" , 
#    0x90: "COMMAND_CLASS_ENERGY_PRODUCTION", 
#    0x82: "COMMAND_CLASS_HAIL", 
#    0x87: "COMMAND_CLASS_INDICATOR", 
#    0x89: "COMMAND_CLASS_LANGUAGE", 
#    0x76: "COMMAND_CLASS_LOCK", 
#    0x72: "COMMAND_CLASS_MANUFACTURER_SPECIFIC", 
#    0x32: "COMMAND_CLASS_METER", 
#    0x35: "COMMAND_CLASS_METER_PULSE", 
#    0x8f: "COMMAND_CLASS_MULTI_CMD", 
#    0x60: "COMMAND_CLASS_MULTI_INSTANCE/CHANNEL", 
#    0x8e: "COMMAND_CLASS_MULTI_INSTANCE_ASSOCIATION", 
#    0x77: "COMMAND_CLASS_NODE_NAMING", 
#    0x00: "COMMAND_CLASS_NO_OPERATION", 
#    0x73: "COMMAND_CLASS_POWERLEVEL", 
#    0x88: "COMMAND_CLASS_PROPRIETARY", 
#    0x75: "COMMAND_CLASS_PROTECTION", 
#    0x2B: "COMMAND_CLASS_SCENE_ACTIVATION", 
#    0x9c: "COMMAND_CLASS_SENSOR_ALARM", 
#    0x30: "COMMAND_CLASS_SENSOR_BINARY", 
#    0x31: "COMMAND_CLASS_SENSOR_MULTILEVEL", 
#    0x27: "COMMAND_CLASS_SWITCH_ALL", 
#    0x25: "COMMAND_CLASS_SWITCH_BINARY", 
#    0x26: "COMMAND_CLASS_SWITCH_MULTILEVEL", 
#    0x28: "COMMAND_CLASS_SWITCH_TOGGLE_BINARY", 
#    0x29: "COMMAND_CLASS_SWITCH_TOGGLE_MULTILEVEL", 
#    0x44: "COMMAND_CLASS_THERMOSTAT_FAN_MODE", 
#    0x45: "COMMAND_CLASS_THERMOSTAT_FAN_STATE", 
#    0x40: "COMMAND_CLASS_THERMOSTAT_MODE", 
#    0x42: "COMMAND_CLASS_THERMOSTAT_OPERATING_STATE", 
#    0x43: "COMMAND_CLASS_THERMOSTAT_SETPOINT", 
#    0x63: "COMMAND_CLASS_USER_CODE", 
#    0x86: "COMMAND_CLASS_VERSION", 
#    0x84: "COMMAND_CLASS_WAKE_UP", 
#    }
    

class Manager(object):
    """Manager as singleton, and singleton options link"""
    
    instance = None
    initialized = False
    
    def __new__(cls, *args, **kargs):
        cls._log = None
        if OPTIONS is not None and OPTIONS.AreLocked:
            if  Manager.instance is None:
                Manager.instance = object.__new__(cls, *args, **kargs)
                Manager.initialized = False
            else :
                Manager.initialized = True
            cls._options = OPTIONS
            cls._watchers = NotificationsWatcher()
            return Manager.instance        
        cls._log = Log()
        cls._log.create("",  False,  True, LogLevel.Debug , LogLevel.Debug, LogLevel.Debug)
        cls._log.write(LogLevel.Error, cls, "Options have not been created and locked. Exiting...")
        exit(1)
        return None
            
    def __init__(self):
        global MANAGER
        if not self.initialized :
            self._nodes = []
            self.drivers = []
            self._xmlData = []
            self._DeviceClass = []
            self.configData = {}
            self._stop = threading.Event()
    #        find, configPath = self._options.GetOptionAsString( "ConfigPath")
    #        self.readXmlDeviceClasses(configPath)
    #        self.manufacturers = Manufacturers(configPath)
    #        self.cmdClassRegistered = CommandClasses(self)
            MANAGER = self

    def __del__(self):
        global MANAGER
        MANAGER =None
        self.instance = None
        self.initialized = False
        self._stop.set()
    
    def Create(self):
        # Create the log file (if enabled)
        find, logging = self._options.GetOptionAsBool( "Logging")
        if not find : logging = False
        find, userPath = self._options.GetOptionAsString( "UserPath")
        if not find : userPath = ""
        find, logFileNameBase = self._options.GetOptionAsString( "LogFileName")
        if not find : logFileNameBase = "OZWEmule_Log.txt"
        find, bAppend = self._options.GetOptionAsBool( "AppendLogFile")
        if not find :  bAppend = False
        find, bConsoleOutput = self._options.GetOptionAsBool( "ConsoleOutput")           
        if not find : bConsoleOutput = True
        find, nSaveLogLevel = self._options.GetOptionAsInt( "SaveLogLevel")
        if not find : nSaveLogLevel = LogLevel.Debug #LogLevel.Detail
        find, nQueueLogLevel = self._options.GetOptionAsInt( "QueueLogLevel")
        if not find : nQueueLogLevel = LogLevel.StreamDetail # LogLevel.Debug
        find, nDumpTrigger = self._options.GetOptionAsInt( "DumpTriggerLevel")
        if not find : nDumpTrigger = LogLevel.Warning
        logFilename = userPath + logFileNameBase
        self._log = Log()
        self._log.create(logFilename, bAppend, bConsoleOutput, nSaveLogLevel, nQueueLogLevel, nDumpTrigger)
        self._log.setLoggingState(logging)
        self._options.setLog(self._log)
        find, configPath = self._options.GetOptionAsString( "ConfigPath")
        self.readXmlDeviceClasses(configPath)
        self.manufacturers = Manufacturers(configPath)
        self.cmdClassRegistered = CommandClasses(self)
        self.cmdClassRegistered.RegisterCommandClasses()
        try :
            self.configData = readJsonFile('../data/config_emulation.json')
            self._log.write(LogLevel.Always, self,"Config for emulation loaded : {0}".format(self.configData))
        except:
            self._log.write(LogLevel.Warning, self,"No correct file config for emulation in data path.")
        self.loadXmlConfig()
#        Scene.ReadScenes()

        self._log.write(LogLevel.Always, self, "OpenZwave-emulator Version {0} Starting Up".format(self.getVersionAsString()))
        
    def GetValAsHex(self, value, nChar = 2):
        print 
        if type(value) != 'list' : data = [value]
        else : data =value
        return GetDataAsHex(data, nChar)
        
    def getVersionAsString(self):
        return "{0}.{1}.{2}".format(ozw_vers_major, ozw_vers_minor, ozw_vers_revision)
        
    def readXmlNetwork(self, fileConf):
        self._xmlData = networkFileConfig(fileConf)
        
    def readXmlDeviceClasses(self, pathConf):
        self._DeviceClass = DeviceClasses(pathConf)
        
    def loadXmlConfig(self):
        dataDir = '../data'
        files = os.listdir(dataDir)
        xmlFormat = r"^zwcfg_0x[0-9,a-f,A-F]{8}.xml$"
        for f in files:
            if re.match(xmlFormat,  f) is not None :
                self.readXmlNetwork(dataDir + "/" + f)
                self._log.write(LogLevel.Always, self, " Loading {0} openzwave file config....".format(dataDir + "/" + f))
                driverData = self._xmlData.getDriver(0)
                print driverData
                homeId = driverData['homeId']
                nodes = self._xmlData.listeNodes()
                for node in nodes :
                    xmlNode = self._xmlData.getNode(node)
                    self.addXmlNode(homeId,  xmlNode['id'],  xmlNode)
                self.drivers.append(Driver(self, self.getNode(homeId, driverData['nodeId']),  driverData))
                print " +++ driver added +++"
    
    def getZwVersion(self):
        if 'controller' in self.configData:
            if 'zwversion' in self.configData['controller']:
                return self.configData['controller']['zwversion']
        return ZWVERSION
    
    def getSerialAPIVersion(self):
        if 'controller' in self.configData:
            if 'serialapiversion' in self.configData['controller']:
                return self.configData['controller']['serialapiversion']
        return SERIALAPIVERSION

    def getRFChipVersion(self):
        if 'controller' in self.configData:
            if 'rfchipversion' in self.configData['controller']:
                return self.configData['controller']['rfchipversion']
        return RFCHIPVERSION

    def getFakeNeighbors(self, nodeId):
        if 'controller' in self.configData:
            if 'fakeneighbors' in self.configData['controller']:
                if str(nodeId) in self.configData['controller']['fakeneighbors']:
                    return self.configData['controller']['fakeneighbors'][str(nodeId)]
        return []
        
    def getEmulNodeData(self, nodeId):
        if 'nodes' in self.configData:
            for n in self.configData['nodes']:
                if 'nodeid' in n and n['nodeid'] == nodeId:
                    return n
        return { "nodeid" : nodeId,
                     "comment" : "Auto comment", 
                    "failed" : False,
                    "timeoutwakeup" : 0,
                    "wakeupduration" : 0,
                    "pollingvalue" : []
                  }
        
    def matchHomeID(self, homeId):
        """Evalue si c'est bien un homeID, retourne le homeID ou None"""
        if type(homeId) in [long,  int] : 
            return "0x%0.8x" %homeId
        homeIDFormat = r"^0x[0-9,a-f]{8}$"
        if re.match(homeIDFormat,  homeId.lower()) is not None :
            return homeId.lower()
        return None

    def addXmlNode(self, homeId, nodeId, xmlNode):
        for n in self._nodes:
            if n.homeId == homeId and n.nodeId == nodeId:
                self._log.write(LogLevel.Warning, self, "Node {0} on homeId {1} from xml config file allready exist, abording add.".format(nodeId,  homeId))
                return None
        node = Node(self,  homeId,  nodeId, xmlNode)
        self._nodes.append(node)
        self._log.write(LogLevel.Info, self, "Node {0} on homeId {1} added from xml config file.".format(nodeId,  homeId))
        
    def GetCommandClassId(self, cmdClass):
        return self.cmdClassRegistered.GetCommandClassId(cmdClass)
        
    def getNode(self, homeId, nodeId):
        for n in self._nodes:
            if (n.homeId == homeId or self.matchHomeID(n.homeId) == homeId) and n.nodeId == nodeId :
                return n
        return None
    
    def getListNodeId(self, homeId):
        listN = []
        for n in self._nodes:
            if n.homeId == homeId  :
                listN.append(n.nodeId)
        return listN
    
    def Addwatcher(self, libnotification,  pycallback):
        if self._watchers.addWatcher(libnotification, pycallback):
            self._log.write(LogLevel.Always, self, "Adding a watcher to {0}".format(pycallback))
            return True
        else :
            self._log.write(LogLevel.Warning, self, "Watcher {0} all ready exist, not Adding".format(pycallback))
            return False

    def AddDriver(self, serialport):
        if self.drivers:
            for driver in self.drivers:
                if driver.serialport is None: # Object Driver not assigned and ready to set serialport
                    driver.setSerialport(serialport)
                    self._log.write(LogLevel.Info, self, "Added driver for controller {0}".format(serialport))
                    driver.Start()
                    return True
                elif driver.serialport == serialport: 
                    self._log.write(LogLevel.Warning, self, "Cannot add driver for controller {0} - driver already exists".format(serialport))
                    return False
            self._log.write(LogLevel.Warning, self, "Cannot add driver for controller {0} - no emulate driver available".format(serialport))
            return False
        else: 
            self._log.write(LogLevel.Info, Warning, "Cannot add driver for controller {0} - no emulate driver loaded".format(serialport))
            return False
    
    def GetDriver(self, homeId):
        for driver in self.drivers:
            if homeId == driver.homeId : return driver
        return None
    
    def SetDriverReady(self, driver, success):
        if success:
            self._log.write( LogLevel.Info, self,  "     Driver with Home ID of {0} is now ready.".format(self.matchHomeID(driver.xmlData['homeId'])))
            self._log.write( LogLevel.Info, "" );
            notify = Notification(NotificationType.DriverReady, driver)
            self._watchers.dispatchNotification(notify)

    def IsSupportedCommandClasses(self,  clsId):
        return self.cmdClassRegistered.IsSupported(clsId)
    
    def SetProductDetails(self, node, manufacturerId, productType, productId):
        manufacturerName = "Unknown: id=%.4x"%manufacturerId
        productName = "Unknown: type=%.4x, id=%.4x"%(productType, productId)
        configPath = ""
        # Try to get the real manufacturer and product names
        manufacturer = self.manufacturers.getManufacturer(manufacturerId)
        if manufacturer:
            # Replace the id with the real name
            manufacturerName = manufacturer['name']
            # Get the product
            for p in manufacturer['products']:
                if (int(productId,  16) == int(p['id'], 16)) and (int(productType,  16) == int(p['type'],  16)):
                    productName = p['name']
                    configPath = p['config'] if 'config' in p else ""
        # Set the values into the node
        # Only set the manufacturer and product name if they are
        # empty - we don't want to overwrite any user defined names.
        if node.GetManufacturerName == "" :
            node.SetManufacturerName(manufacturerName )
        if node.GetProductName == "":
            node.SetProductName(productName)
        node.SetManufacturerId("%.4x"%manufacturerId)
        node.SetProductType("%.4x"%productType)
        node.SetProductId(  "%.4x"%productId )
        return configPath
            
"""
        # // Configuration
        void WriteConfig(uint32_t homeid)
        Options* GetOptions()
        # // Drivers
        bint AddDriver(string serialport)
        bint RemoveDriver(string controllerPath)
        uint8_t GetControllerNodeId(uint32_t homeid)
        uint8_t GetSUCNodeId(uint32_t homeid)
        bint IsPrimaryController(uint32_t homeid)
        bint IsStaticUpdateController(uint32_t homeid)
        bint IsBridgeController(uint32_t homeid)
        string GetLibraryVersion(uint32_t homeid)
        string GetLibraryTypeName(uint32_t homeid)
        int32_t GetSendQueueCount( uint32_t homeId )
        void LogDriverStatistics( uint32_t homeId )
        void GetDriverStatistics( uint32_t homeId, DriverData* data )
        void GetNodeStatistics( uint32_t homeId, uint8_t nodeid, NodeData* data )
        ControllerInterface GetControllerInterfaceType( uint32_t homeId )
        string GetControllerPath( uint32_t homeId )
        # // Network
        void TestNetworkNode( uint32_t homeId, uint8_t nodeId, uint32_t count )
        void TestNetwork( uint32_t homeId, uint32_t count )
        void HealNetworkNode( uint32_t homeId, uint32_t nodeId, bool _doRR )
        void HealNetwork( uint32_t homeId, bool doRR)
        # // Polling
        uint32_t GetPollInterval()
        void SetPollInterval(uint32_t milliseconds, bIntervalBetweenPolls)
        bint EnablePoll(ValueID& valueId, uint8_t intensity)
        bool DisablePoll(ValueID& valueId)
        bool isPolled(ValueID& valueId)
        void SetPollIntensity( ValueID& valueId, uint8_t intensity)
        uint8_t GetPollIntensity(ValueID& valueId)
        # // Node Information
        bool RefreshNodeInfo(uint32_t homeid, uint8_t nodeid)
        bool RequestNodeState(uint32_t homeid, uint8_t nodeid)
        bool RequestNodeDynamic( uint32_t homeId, uint8_t nodeId )
        bool IsNodeListeningDevice(uint32_t homeid, uint8_t nodeid)
        bool IsNodeFrequentListeningDevice( uint32_t homeId, uint8_t nodeId )
        bool IsNodeBeamingDevice( uint32_t homeId, uint8_t nodeId )
        bool IsNodeRoutingDevice(uint32_t homeid, uint8_t nodeid)
        bool IsNodeSecurityDevice( uint32_t homeId, uint8_t nodeId )
        uint32_t GetNodeMaxBaudRate(uint32_t homeid, uint8_t nodeid)
        uint8_t GetNodeVersion(uint32_t homeid, uint8_t nodeid)
        uint8_t GetNodeSecurity(uint32_t homeid, uint8_t nodeid)
        uint8_t GetNodeBasic(uint32_t homeid, uint8_t nodeid)
        uint8_t GetNodeGeneric(uint32_t homeid, uint8_t nodeid)
        uint8_t GetNodeSpecific(uint32_t homeid, uint8_t nodeid)
        string GetNodeType(uint32_t homeid, uint8_t nodeid)
        uint32_t GetNodeNeighbors(uint32_t homeid, uint8_t nodeid, uint8_t** nodeNeighbors)
        string GetNodeManufacturerName(uint32_t homeid, uint8_t nodeid)
        string GetNodeProductName(uint32_t homeid, uint8_t nodeid)
        string GetNodeName(uint32_t homeid, uint8_t nodeid)
        string GetNodeLocation(uint32_t homeid, uint8_t nodeid)
        string GetNodeManufacturerId(uint32_t homeid, uint8_t nodeid)
        string GetNodeProductType(uint32_t homeid, uint8_t nodeid)
        string GetNodeProductId(uint32_t homeid, uint8_t nodeid)
        void SetNodeManufacturerName(uint32_t homeid, uint8_t nodeid, string manufacturerName)
        void SetNodeProductName(uint32_t homeid, uint8_t nodeid, string productName)
        void SetNodeName(uint32_t homeid, uint8_t nodeid, string productName)
        void SetNodeLocation(uint32_t homeid, uint8_t nodeid, string location)
        void SetNodeOn(uint32_t homeid, uint8_t nodeid)
        void SetNodeOff(uint32_t homeid, uint8_t nodeid)
        void SetNodeLevel(uint32_t homeid, uint8_t nodeid, uint8_t level)
        bool IsNodeInfoReceived(uint32_t homeid, uint8_t nodeid)
        bool GetNodeClassInformation( uint32_t homeId, uint8_t nodeId, uint8_t commandClassId,
                          string *className, uint8_t *classVersion)
        bool IsNodeAwake(uint32_t homeid, uint8_t nodeid)
        bool IsNodeFailed(uint32_t homeid, uint8_t nodeid)
        string GetNodeQueryStage(uint32_t homeid, uint8_t nodeid)
        # // Values
        string GetValueLabel(ValueID& valueid)
        void SetValueLabel(ValueID& valueid, string value)
        string GetValueUnits(ValueID& valueid)
        void SetValueUnits(ValueID& valueid, string value)
        string GetValueHelp(ValueID& valueid)
        void SetValueHelp(ValueID& valueid, string value)
        uint32_t GetValueMin(ValueID& valueid)
        uint32_t GetValueMax(ValueID& valueid)
        bool IsValueReadOnly(ValueID& valueid)
        bool IsValueWriteOnly(ValueID& valueid)
        bool IsValueSet(ValueID& valueid)
        bool IsValuePolled( ValueID& valueid )
        bool GetValueAsBool(ValueID& valueid, bool* o_value)
        bool GetValueAsByte(ValueID& valueid, uint8_t* o_value)
        bool GetValueAsFloat(ValueID& valueid, float* o_value)
        bool GetValueAsInt(ValueID& valueid, int32_t* o_value)
        bool GetValueAsShort(ValueID& valueid, int16_t* o_value)
        bool GetValueAsRaw(ValueID& valueid, uint8_t** o_value, uint8_t* o_length )
        bool GetValueAsString(ValueID& valueid, string* o_value)
        bool GetValueListSelection(ValueID& valueid, string* o_value)
        bool GetValueListSelection(ValueID& valueid, int32_t* o_value)
        bool GetValueListItems(ValueID& valueid, vector[string]* o_value)
        bool SetValue(ValueID& valueid, bool value)
        bool SetValue(ValueID& valueid, uint8_t value)
        bool SetValue(ValueID& valueid, float value)
        bool SetValue(ValueID& valueid, int32_t value)
        bool SetValue(ValueID& valueid, int16_t value)
        bool SetValue(ValueID& valueid, uint8_t* value, uint8_t length)
        bool SetValue(ValueID& valueid, string value)
        bool SetValueListSelection(ValueID& valueid, string selecteditem)
        bool RefreshValue(ValueID& valueid)
        void SetChangeVerified(ValueID& valueid, bool verify)
        bool PressButton(ValueID& valueid)
        bool ReleaseButton(ValueID& valueid)
        bool GetValueFloatPrecision(ValueID& valueid, uint8_t* o_value)
        # // Climate Control
        uint8_t GetNumSwitchPoints(ValueID& valueid)
        bool SetSwitchPoint(ValueID& valueid, uint8_t hours, uint8_t minutes, uint8_t setback)
        bool RemoveSwitchPoint(ValueID& valueid, uint8_t hours, uint8_t minutes)
        bool ClearSwitchPoints(ValueID& valueid)
        bool GetSwitchPoint(ValueID& valueid, uint8_t idx, uint8_t* o_hours, uint8_t* o_minutes, int8_t* o_setback)
        # // SwitchAll
        void SwitchAllOn(uint32_t homeid)
        void SwitchAllOff(uint32_t homeid)
        # // Configuration Parameters
        bool SetConfigParam(uint32_t homeid, uint8_t nodeid, uint8_t param, uint32_t value, uint8_t size)
        void RequestConfigParam(uint32_t homeid, uint8_t nodeid, uint8_t aram)
        void RequestAllConfigParams(uint32_t homeid, uint8_t nodeid)
        # // Groups
        uint8_t GetNumGroups(uint32_t homeid, uint8_t nodeid)
        uint32_t GetAssociations(uint32_t homeid, uint8_t nodeid, uint8_t groupidx, uint8_t** o_associations)
        uint8_t GetMaxAssociations(uint32_t homeid, uint8_t nodeid, uint8_t groupidx)
        string GetGroupLabel(uint32_t homeid, uint8_t nodeid, uint8_t groupidx)
        void AddAssociation(uint32_t homeid, uint8_t nodeid, uint8_t groupidx, uint8_t targetnodeid)
        void RemoveAssociation(uint32_t homeid, uint8_t nodeid, uint8_t groupidx, uint8_t targetnodeid)
        bool AddWatcher(pfnOnNotification_t notification, void* context)
        bool RemoveWatcher(pfnOnNotification_t notification, void* context)
        # void NotifyWatchers(Notification*) 
        # // Controller Commands
        void ResetController(uint32_t homeid)
        void SoftReset(uint32_t homeid)
        bool BeginControllerCommand(uint32_t homeid, ControllerCommand _command, pfnControllerCallback_t _callback, void* _context, bool _highPower, uint8_t _nodeId, uint8_t _arg )
        bool CancelControllerCommand(uint32_t homeid)
        # // Scene commands
        uint8_t GetNumScenes()
        uint8_t GetAllScenes(uint8_t** sceneIds)
        uint8_t CreateScene()
        void RemoveAllScenes( uint32_t _homeId )
        bool RemoveScene(uint8_t sceneId)
        bool AddSceneValue( uint8_t sceneId, ValueID& valueId, bool value)
        bool AddSceneValue( uint8_t sceneId, ValueID& valueId, uint8_t value)
        bool AddSceneValue( uint8_t sceneId, ValueID& valueId, float value )
        bool AddSceneValue( uint8_t sceneId, ValueID& valueId, int32_t value )
        bool AddSceneValue( uint8_t sceneId, ValueID& valueId, int16_t value )
        bool AddSceneValue( uint8_t sceneId, ValueID& valueId, string value )
        bool AddSceneValueListSelection( uint8_t sceneId, ValueID& valueId, string value )
        bool AddSceneValueListSelection( uint8_t sceneId, ValueID& valueId, int32_t value )
        bool RemoveSceneValue( uint8_t sceneId, ValueID& valueId )
        int SceneGetValues( uint8_t sceneId, vector[ValueID]* o_value )
        bool SceneGetValueAsBool( uint8_t sceneId, ValueID& valueId, bool* value )
        bool SceneGetValueAsByte( uint8_t sceneId, ValueID& valueId, uint8_t* o_value )
        bool SceneGetValueAsFloat( uint8_t sceneId, ValueID& valueId, float* o_value )
        bool SceneGetValueAsInt( uint8_t sceneId, ValueID& valueId, int32_t* o_value )
        bool SceneGetValueAsShort( uint8_t sceneId, ValueID& valueId, int16_t* o_value )
        bool SceneGetValueAsString( uint8_t sceneId, ValueID& valueId, string* o_value )
        bool SceneGetValueListSelection( uint8_t sceneId, ValueID& valueId, string* o_value )
        bool SceneGetValueListSelection( uint8_t sceneId, ValueID& valueId, int32_t* o_value )
        bool SetSceneValue( uint8_t sceneId, ValueID& valueId, bool value )
        bool SetSceneValue( uint8_t sceneId, ValueID& valueId, uint8_t value )
        bool SetSceneValue( uint8_t sceneId, ValueID& valueId, float value )
        bool SetSceneValue( uint8_t sceneId, ValueID& valueId, int32_t value )
        bool SetSceneValue( uint8_t sceneId, ValueID& valueId, int16_t value )
        bool SetSceneValue( uint8_t sceneId, ValueID& valueId, string value )
        bool SetSceneValueListSelection( uint8_t sceneId, ValueID& valueId, string value )
        bool SetSceneValueListSelection( uint8_t sceneId, ValueID& valueId, int32_t value )
        string GetSceneLabel( uint8_t sceneId )
        void SetSceneLabel( uint8_t sceneId, string value )
        bool SceneExists( uint8_t sceneId )
        bool ActivateScene( uint8_t sceneId )
        
"""

        
if __name__ == "__main__":
    
    def notif_callback(notification, callback):
        """
        Notification callback to the C++ library

        """
        from libopenzwave import PyNotifications
        
        print 'recu dans notif_callback : {0}'.format(notification)
        n = {'notificationType' : PyNotifications[notification.GetType()],
             'homeId' : notification.GetHomeId(),
             'nodeId' : notification.GetNodeId(),
    #         'context' : "%s" % (<object>_context),
             }
        if notification.GetType() == NotificationType.Group:
            n['groupIdx'] = notification.GetGroupIdx()
        elif notification.GetType() == NotificationType.NodeEvent:
            n['event'] = notification.GetEvent()
        elif notification.GetType() == NotificationType.Notification:
            n['notificationCode'] = NotificationType.notification.GetNotification()
        elif notification.GetType() in (NotificationType.CreateButton, NotificationType.DeleteButton, NotificationType.ButtonOn, NotificationType.ButtonOff):
            n['buttonId'] = notification.GetButtonId()
        elif notification.GetType() == NotificationType.SceneEvent:
            n['sceneId'] = notification.GetSceneId()
        addValueId(notification._obj, n)
        #logging.debug("++++++++++++ libopenzwave.notif_callback : notification %s" % n)
        callback(n)
    
    def addValueId(obj, n):
#        v = ValueID(v)
        n['valueId'] = {'homeId' : obj.homeId,
                        'nodeId' : obj.nodeId,
                        'commandClass' :obj.GetClassInformation()['name'],
                        'instance' : obj.instance,
                        'index' : obj.index,
                        'id' : obj.GetId(),
                        'genre' : ValueGenre().getFromVal(obj.genre),
                        'type' :  ValueType().getFromVal(obj.type),
                        'value' : obj.getVal(), 
                        'label' : obj.label,
                        'units' : obj.units,
                        'readOnly': obj.readOnly  #manager.IsValueReadOnly(v),
                        }
    
    class API :
        def pyCallback(self,  notification):
            print 'recu dans le callback : {0}'.format(notification)
    print "************** start in main of manager.py **************"
    OPTIONS.create("../openzwave/config", "", "--logging true --LogFileName test.log")
    print "NotifyTransactions :", OPTIONS.AddOptionBool('NotifyTransactions',  True)
    OPTIONS.Lock()
    manager = Manager()
    manager.Create()
    manager.Addwatcher(notif_callback, API().pyCallback)
    manager.AddDriver('/tmp/ttyS1')
    
    import time
    while True and not manager._stop.isSet():
        try :
            time.sleep(.01)
        except KeyboardInterrupt:
            manager._stop.set()
    for driver in manager.drivers:
        driver.running = False
#    notify = Notification(NotificationType.ValueAdded, value)
#    manager._watchers.dispatchNotification(notify)