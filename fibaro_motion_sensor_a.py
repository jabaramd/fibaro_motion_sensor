#!/usr/bin/env python
# fibaro_motion_sensor_a.py
# Copyright (C) ContinuumBridge Limited, 2014-2015 - All Rights Reserved
# Written by Peter Claydon
#
ModuleName               = "fibaro_motion_sensor"
BATTERY_CHECK_INTERVAL   = 10800      # How often to check battery (secs) = 3 hours
SENSOR_POLL_INTERVAL     = 600        # How often to request sensor values = 10 mins
TIME_CUTOFF              = 1800       # Data older than this is considered "stale"

import sys
import time
import json
import os
from pprint import pprint
from cbcommslib import CbAdaptor
from cbconfig import *
from twisted.internet import threads
from twisted.internet import reactor

class Adaptor(CbAdaptor):
    def __init__(self, argv):
        self.status =                "ok"
        self.state =                 "stopped"
        self.apps =                  {"binary_sensor": [],
                                      "temperature": [],
                                      "luminance": [],
                                      "battery": [],
                                      "connected": []}
        self.lastTemperatureTime =   0
        self.lastHumidityTime =      0
        self.lastLuminanceTime =     0
        self.lastBinaryTime =        0
        self.lastBatteryTime =       0
        # super's __init__ must be called:
        #super(Adaptor, self).__init__(argv)
        CbAdaptor.__init__(self, argv)
 
    def setState(self, action):
        #self.cbLog("debug", "setting state to: " + action)
        # error is only ever set from the running state, so set back to running if error is cleared
        if action == "error":
            self.state == "error"
        elif action == "clear_error":
            self.state = "running"
        else:
            self.state = action
        msg = {"id": self.id,
               "status": "state",
               "state": self.state}
        self.sendManagerMessage(msg)

    def sendCharacteristic(self, characteristic, data, timeStamp):
        msg = {"id": self.id,
               "content": "characteristic",
               "characteristic": characteristic,
               "data": data,
               "timeStamp": timeStamp}
        for a in self.apps[characteristic]:
            self.sendMessage(msg, a)

    def checkBattery(self):
        self.cbLog("debug", "checkBattery")
        cmd = {"id": self.id,
               "request": "post",
               "address": self.addr,
               "instance": "0",
               "commandClass": "128",
               "action": "Get",
               "value": ""
              }
        self.sendZwaveMessage(cmd)
        reactor.callLater(BATTERY_CHECK_INTERVAL, self.checkBattery)

    def pollSensors(self):
        cmd = {"id": self.id,
               "request": "post",
               "address": self.addr,
               "instance": "0",
               "commandClass": "49",
               "action": "Get",
               "value": ""
              }
        self.sendZwaveMessage(cmd)
        reactor.callLater(SENSOR_POLL_INTERVAL, self.pollSensors)

    def forceInterview(self):
        self.cbLog("debug", "forceInterview")
        cmd = {"id": self.id,
               "request": "force_interview",
               "address": self.addr
              }
        self.sendZwaveMessage(cmd)

    def checkConnected(self):
        self.cbLog("debug", "checkConnected, updateTime: " + str(self.updateTime) + ", lastUpdateTime: " + str(self.lastUpdateTime))
        if self.updateTime == self.lastUpdateTime:
            self.connected = False
        else:
            self.connected = True
        self.sendCharacteristic("connected", self.connected, time.time())
        self.lastUpdateTime = self.updateTime
        reactor.callLater(SENSOR_POLL_INTERVAL * 2, self.checkConnected)

    def onZwaveMessage(self, message):
        self.cbLog("debug", "onZwaveMessage, message: " + str(json.dumps(message, indent=4)))
        if message["content"] == "init":
            self.updateTime = 0
            self.lastUpdateTime = time.time()
            # Alarm command class
            cmd = {"id": self.id,
                   "request": "get",
                   "address": self.addr,
                   "instance": "0",
                   "commandClass": "48",
                   "value": "1"
                  }
            self.sendZwaveMessage(cmd)
            # Temperature
            cmd = {"id": self.id,
                   "request": "get",
                   "address": self.addr,
                   "instance": "0",
                   "commandClass": "49",
                   "value": "1"
                  }
            self.sendZwaveMessage(cmd)
            # luminance
            cmd = {"id": self.id,
                   "request": "get",
                   "address": self.addr,
                   "instance": "0",
                   "commandClass": "49",
                   "value": "3"
                  }
            self.sendZwaveMessage(cmd)
            # Battery
            cmd = {"id": self.id,
                   "request": "get",
                   "address": self.addr,
                   "instance": "0",
                   "commandClass": "128"
                  }
            self.sendZwaveMessage(cmd)
            # Associate PIR alarm with this controller
            cmd = {"id": self.id,
                   "request": "post",
                   "address": self.addr,
                   "instance": "0",
                   "commandClass": "133",
                   "action": "Set",
                   "value": "1,1"
                  }
            self.sendZwaveMessage(cmd)
            # Associate temperature/luminance with this controller
            cmd = {"id": self.id,
                   "request": "post",
                   "address": self.addr,
                   "instance": "0",
                   "commandClass": "133",
                   "action": "Set",
                   "value": "2,1"
                  }
            self.sendZwaveMessage(cmd)
            # Associate temperature/luminance with this controller
            cmd = {"id": self.id,
                   "request": "post",
                   "address": self.addr,
                   "instance": "0",
                   "commandClass": "133",
                   "action": "Set",
                   "value": "3,1"
                  }
            self.sendZwaveMessage(cmd)
            # Turn off LED for motion
            cmd = {"id": self.id,
                   "request": "post",
                   "address": self.addr,
                   "instance": "0",
                   "commandClass": "112",
                   "action": "Set",
                   "value": "80,0,1"
                  }
            self.sendZwaveMessage(cmd)
            # Turn off LED for tamper
            cmd = {"id": self.id,
                   "request": "post",
                   "address": self.addr,
                   "instance": "0",
                   "commandClass": "112",
                   "action": "Set",
                   "value": "89,0,1"
                  }
            self.sendZwaveMessage(cmd)
            # Change motion cancellation delay from 30s to 60s
            cmd = {"id": self.id,
                   "request": "post",
                   "address": self.addr,
                   "instance": "0",
                   "commandClass": "112",
                   "action": "Set",
                   "value": "6,60,2"
                  }
            self.sendZwaveMessage(cmd)
            # Wakeup every 5 minutes
            cmd = {"id": self.id,
                   "request": "post",
                   "address": self.addr,
                   "instance": "0",
                   "commandClass": "132",
                   "action": "Set",
                   "value": "300,1"
                  }
            self.sendZwaveMessage(cmd)
            reactor.callLater(300, self.checkBattery)
            reactor.callLater(30, self.pollSensors)
            reactor.callLater(300, self.checkConnected)
        elif message["content"] == "data":
            try:
                if message["commandClass"] == "49":
                    if message["value"] == "1":
                        temperature = message["data"]["val"]["value"] 
                        updateTime = message["data"]["val"]["updateTime"] 
                        # Only send if we don't already have an update from this time and the update is recent (not stale after restart)
                        if updateTime != self.lastTemperatureTime and time.time() - updateTime < TIME_CUTOFF:
                            self.cbLog("debug", "onZwaveMessage, temperature: " + str(temperature))
                            self.sendCharacteristic("temperature", temperature, updateTime)
                            self.lastTemperatureTime = updateTime
                    elif message["value"] == "3":
                        luminance = message["data"]["val"]["value"] 
                        updateTime = message["data"]["val"]["updateTime"] 
                        if updateTime != self.lastLuminanceTime and time.time() - updateTime < TIME_CUTOFF:
                            self.cbLog("debug", "onZwaveMessage, luminance: " + str(luminance))
                            self.sendCharacteristic("luminance", luminance, time.time())
                            self.lastLuminanceTime = updateTime
                    elif message["value"] == "5":
                        humidity = message["data"]["val"]["value"] 
                        updateTime = message["data"]["val"]["updateTime"] 
                        if updateTime != self.lastHumidityTime and time.time() - updateTime < TIME_CUTOFF:
                            self.cbLog("debug", "onZwaveMessage, humidity: " + str(humidity))
                            self.sendCharacteristic("humidity", humidity, time.time())
                            self.lastHumidityTime = updateTime
                elif message["commandClass"] == "48":
                    if message["value"] == "1":
                        updateTime = message["data"]["level"]["updateTime"]
                        if updateTime != self.lastBinaryTime and time.time() - updateTime < TIME_CUTOFF:
                            if message["data"]["level"]["value"]:
                                b = "on"
                            else:
                                b = "off"
                            self.cbLog("debug", "onZwaveMessage, alarm: " + b)
                            self.sendCharacteristic("binary_sensor", b, time.time())
                            self.lastBinaryTime = updateTime
                elif message["commandClass"] == "128":
                    updateTime = message["data"]["last"]["updateTime"]
                    if (updateTime != self.lastBatteryTime) and (time.time() - updateTime < TIME_CUTOFF):
                        battery = message["data"]["last"]["value"] 
                        self.cbLog("debug", "battery: " + str(battery))
                        msg = {"id": self.id,
                               "status": "battery_level",
                               "battery_level": battery}
                        self.sendManagerMessage(msg)
                        self.sendCharacteristic("battery", battery, time.time())
                        self.lastBatteryTime = updateTime
                self.updateTime = message["data"]["updateTime"]
            except Exception as ex:
                self.cbLog("warning", "onZwaveMessage, unexpected message: " + str(message))
                self.cbLog("warning", "Exception: " + str(type(ex)) + str(ex.args))

    def onAppInit(self, message):
        self.cbLog("debug", "onAppInit, message: " + str(message))
        resp = {"name": self.name,
                "id": self.id,
                "status": "ok",
                "service": [{"characteristic": "binary_sensor", "interval": 0, "type": "pir"},
                            {"characteristic": "temperature", "interval": 600},
                            {"characteristic": "luminance", "interval": 600},
                            {"characteristic": "battery", "interval": 600},
                            {"characteristic": "connected", "interval": 600}],
                "content": "service"}
        self.sendMessage(resp, message["id"])
        self.setState("running")

    def onAppRequest(self, message):
        # Switch off anything that already exists for this app
        for a in self.apps:
            if message["id"] in self.apps[a]:
                self.apps[a].remove(message["id"])
        # Now update details based on the message
        for f in message["service"]:
            if message["id"] not in self.apps[f["characteristic"]]:
                self.apps[f["characteristic"]].append(message["id"])
        self.cbLog("debug", "apps: " + str(self.apps))

    def onAppCommand(self, message):
        if "data" not in message:
            self.cbLog("warning", "app message without data: " + str(message))
        else:
            self.cbLog("warning", "This is a sensor. Message not understood: " +  str(message))

    def onAction(self, action):
        self.cbLog("debug", "onAction")
        if action == "interview":
            self.forceInterview()
        else:
            self.cbLog("warning", "onAction. Unrecognised action: " +  str(action))

    def onConfigureMessage(self, config):
        #self.cbLog("debug", "onConfigureMessage, config: " + str(config))
        """Config is based on what apps are to be connected.
            May be called again if there is a new configuration, which
            could be because a new app has been added.
        """
        self.setState("starting")

if __name__ == '__main__':
    Adaptor(sys.argv)
