#!/usr/bin/env python
# Created: July 2011
# Author: David Weiss
#
# An example bot that implements the same logic as the provided
# GreedyBot in the Ants distribution. It first looks for nearby food,
# then for nearby enemies, and finally just moves randomly.

import logging
import random
import sys

from antsbot import AntsBot
from worldstate import AIM, AntStatus, AntWorld

class GreedyBot(AntsBot):
    def get_direction(self, ant):
        '''Finds a direction for this ant to move in according to the food, enemy, exploration routine.'''
        
        # Get the list of directions towards food, enemy, and random
        rand_dirs = AIM.keys()
        random.shuffle(rand_dirs)
        dirs = (ant.toward(ant.closest_food()) + ant.toward(ant.closest_enemy()) + rand_dirs)
        
        # Get the first passable direction from that long list.
        d = ant.get_passable_direction(dirs)
        return d

    # Main logic
    def do_turn(self):
        # Run the routine for each living ant independently.
        for ant in self.world.ants:
            if ant.status == AntStatus.ALIVE:
                ant.direction = self.get_direction(ant)


# Main section allowing for dual use either with the standard engine
# or the LocalEngine. If no arguments are given, it calls
# AntsBot.Run() to run as a stand alone process, communicating via
# stdin/stdout. However, if arguments are given, it passes them to
# LocalEngine and creates two instances of GreedyBot to play against
# one another.
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
            engine.AddBot(GreedyBot(engine.GetWorld()))
            engine.AddBot(GreedyBot(engine.GetWorld()))
            engine.Run(sys.argv)
            
        else: # Run as stand-alone process
            bot = GreedyBot(AntWorld())
            bot._run()

    except KeyboardInterrupt:
        print('ctrl-c, leaving ...')
