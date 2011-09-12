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
from localengine import LocalEngine
from worldstate import AIM, AntStatus, AntWorld

class GreedyBot(AntsBot):
    def closest_food(self, ant):
        '''Get the closest food, or None if no food is in sight.'''
        dists = ant.sort_by_distance(ant.world.food)
        if dists:
            return dists[0][1]
        else:
            return None

    def closest_enemy(self, ant):
        '''Get the closest enemy, or None if no enemy is in sight.'''
        dists = ant.sort_by_distance(ant.world.enemies)
        if dists:
            return dists[0][1]
        else:
            return None

    def get_passable_direction(self, ant, dirs):
        '''Filter a list of NSEW directions to remove directions that are not passable from an ant's current position. Returns the FIRST direction that is passable.'''
        if dirs is None:
            return None

        for d in dirs:
            l = self.world.next_position(ant.location, d)
            if self.world.passable(l) and self.world.unoccupied(l):
                self.world.L.debug("ant %d: move %s: %s->%s is not blocked" %
                                (ant.ant_id, d, str(ant.location),str(l)))
                return d

        return None

    def get_direction(self, ant):
        '''Finds a direction for this ant to move in according to the food, enemy, exploration routine.'''
        
        # Get the list of directions towards food, enemy, and random
        rand_dirs = AIM.keys()
        random.shuffle(rand_dirs)
        dirs = (ant.toward(self.closest_food(ant)) + ant.toward(self.closest_enemy(ant)) + rand_dirs)
        
        # Get the first passable direction from that long list.
        d = self.get_passable_direction(ant, dirs)
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
            bot._run()

    except KeyboardInterrupt:
        print('ctrl-c, leaving ...')
