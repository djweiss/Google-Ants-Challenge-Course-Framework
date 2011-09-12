#!/usr/bin/env python
# Created: July 2011
# Author: David Weiss
#
# Sets up a default global logger named L for shorthand, which logs a
# nice format to the console.
              
import os,sys,logging

# initialize logging
def GetDefaultLogger(name="default", level=logging.DEBUG,handler=None):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if handler == None:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '[%(levelname)s] ' +
            '%(filename)s:%(lineno)d:%(funcName)s: - %(message)s')
        handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger

global L
L = GetDefaultLogger(level=logging.DEBUG)  

