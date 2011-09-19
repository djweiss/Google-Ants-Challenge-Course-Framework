#!/usr/bin/env python
# Created: September 2011
# Author: Jennifer Gillenwater
#
# An example deterministic finite automaton (DFA) bot.

import sys

from antsbot import AntsBot
from worldstate import AIM, AntStatus, AntWorld

class StillBot(AntsBot):
    def __init__(self, world):
        AntsBot.__init__(self,world)
    
    # Main logic
    def do_turn(self):
        # Run the routine for each living ant independently.
        for ant in self.world.ants:
            ant.direction = None
                

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
            engine.AddBot(DFABot(engine.GetWorld()))
            engine.AddBot(GreedyBot(engine.GetWorld()))
            engine.Run(sys.argv)
            
        else: # Run as stand-alone process
            bot = DFABot(AntWorld())
            bot._run()

    except KeyboardInterrupt:
        print('ctrl-c, leaving ...')
