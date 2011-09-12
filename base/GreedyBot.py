#!/usr/bin/env python
# Created: July 2011
# Author: David Weiss
#
# An example bot that implements the same logic as the provided
# GreedyBot in the Ants distribution. It first looks for nearby food,
# then for nearby enemies, and finally just moves randomly.

from random import shuffle
from worldstate import *
from antsbot import *
from localengine import *
import logging
import sys

class GreedyBot(AntsBot):

    # Filters a list of NSEW directions to remove directions that are
    # not passable from an ant's current position. Returns the FIRST
    # direction that is passable.
    def GetPassableDirection(self, ant, dirs):
        if dirs == None:
            return None

        for d in dirs:
            l = self.world.NextPosition(ant.location, d)
            if self.world.Passable(l) and self.world.Unoccupied(l):
                self.world.L.debug("ant %d: move %s: %s->%s is not blocked" %
                                (ant.ant_id, d, str(ant.location),str(l)))
                return d

        return None

    # Finds a direction for this ant to move in according to the food,
    # enemy, exploration routine.
    def GetDirection(self, ant):
        
        # Get the list of directions towards food, enemy, and random
        food = ant.FindClosestFood()
        enemy = ant.FindClosestEnemy()
        rand_dirs = AIM.keys()
        shuffle(rand_dirs)
        dirs = (ant.Directions(food) + ant.Directions(enemy) + rand_dirs)
        
        # Get the first passable direction from that long list.
        d = self.GetPassableDirection(ant, dirs)
        return d

    # Main logic
    def DoTurn(self):

        # Run the routine for each living ant independently.
        for ant in self.world.ant_list:
            if ant.status == AntStatus.ALIVE:
                ant.direction = self.GetDirection(ant)


# Main section allowing for dual use either with the standard engine
# or the LocalEngine. If no arguments are given, it calls
# AntsBot.Run() to run as a stand alone process, communicating via
# stdin/stdout. However, if arguments are given, it passes them to
# LocalEngine and creates two instances of GreedyBot to play against
# one another.
if __name__ == '__main__':

    # From Ants distribution: use pyco to speed up all code.
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass

    try:
        if len(sys.argv) > 1: # Run LocalEngine version
            engine = LocalEngine()
            engine.AddBot(GreedyBot(engine.GetWorld()))
            engine.AddBot(GreedyBot(engine.GetWorld()))
            engine.Run(sys.argv)
            
        else: # Run as stand-alone process
            bot = GreedyBot(AntWorld())
            bot.Run()

    except KeyboardInterrupt:
        print('ctrl-c, leaving ...')
