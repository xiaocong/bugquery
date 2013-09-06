#!/usr/bin/env python

import os


class ServerConfig(object):

    '''
    '''

    def __init__(self):
        self.Config = self.readConfigs(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "server.config"))

    def readConfigs(self, file):
        config = {}
        configFile = open(file, 'r')
        allLines = configFile.readlines()
        for line in allLines:
            if line != None and len(line) > 0 and (not line.startswith('#')) and ('=' in line):
                indexEqual = line.find('=')
                key = line[0:indexEqual].strip()
                value = line[indexEqual + 1:].strip()
                config[key] = value
        return config


Config = ServerConfig().Config
