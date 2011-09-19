#!/usr/bin/env python
# Created: September 2011
# Author: Ben Sapp
#
# A skeleton for a general bot using DFA and search talents

import sys

from antsbot import AntsBot
from greedybot import GreedyBot
from worldstate import AIM, AntStatus, AntWorld

class SearchBot(AntsBot):
    def __init__(self, world):
        self.world = world
        
    
    # Main logic
    def do_turn(self):
        # filler: send each ant north
        for a in self.world.ants:
            a.direction = 'n'
        
                

# Main section allowing for dual use either with the standard engine
# or the LocalEngine. If no arguments are given, it calls
# AntsBot.Run() to run as a stand alone process, communicating via
# stdin/stdout. However, if arguments are given, it passes them to
# LocalEngine and creates an instance of DFABot and an instance of
# GreedyBot to play against one another.
if __name__ == '__main__':

    # From Ants distribution: use psyco to speed up all code.
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass

    try:
        if len(sys.argv) > 1: # Run LocalEngine version
            from localengine import LocalEngine
            engine = LocalEngine()
            engine.AddBot(SearchBot(engine.GetWorld()))
            engine.AddBot(GreedyBot(engine.GetWorld()))
            engine.Run(sys.argv)
            
        else: # Run as stand-alone process
            bot = SearchBot(AntWorld())
            bot._run()

    except KeyboardInterrupt:
        print('ctrl-c, leaving ...')
