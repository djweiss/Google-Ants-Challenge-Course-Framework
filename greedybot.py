#!/usr/bin/env python
# Created: July 2011
# Author: David Weiss
#
# An example bot that implements the same logic as the provided
# GreedyBot in the Ants distribution. It first looks for nearby food,
# then for nearby enemies, and finally just moves randomly.
import random

from src.antsbot import AntsBot
from src.worldstate import AIM, AntStatus, AntWorld

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
        next_locations = {}
        for ant in self.world.ants:
            if ant.status == AntStatus.ALIVE:
                ant.direction = self.get_direction(ant)
                
                if ant.direction == 'halt' or ant.direction == None:
                    ant.direction = None
                else:
                    # Basic collision detection: don't land on the same square as another friendly ant.
                    nextpos = self.world.next_position(ant.location, ant.direction) 
                    if nextpos in next_locations.keys():  
                        ant.direction = None
                    else:
                        next_locations[nextpos] = ant.ant_id
        
BOT = GreedyBot
