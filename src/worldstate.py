#!/usr/bin/env python
# Created: July 2011
# Author: David Weiss
#
# A class to replace the "Ants" class for game clients provided by the
# Ants distribution. Unlike "Ants", this class will communicate either
# by stdin/stdout OR with a LocalEngine class, if the "engine"
# parameter is set via the constructor.
#
# The second major difference is that AntsWorld keeps track of the
# player's ants based on messages from the server, so that the game
# state is a list of persistent Ant objects in addition to the
# history-less map data. (The original distribution came only with the
# history-less map data.)
#
# Both AntWorld and Ant provide many helper functions for bots to
# simplify common operations, such as computing distances, finding
# targets, etc.
#
# TODO: AntsWorld should keep track of UNSEEN map elements, which are
# currently unused.

import random
import sys
import traceback

from logutil import *

# Constants used to interpret mapdata. TODO: A more elegant solution.
MY_ANT = 0
ANTS = 0
DEAD = -1
LAND = -2
FOOD = -3
WATER = -4
UNSEEN = -5
MAX_INT=99999999
MAP_RENDER = 'abcdefghijklmnopqrstuvwxyz?!%*.'

# Converts N-S-E-W directions into X-Y vectors.
AIM = {'n': (-1, 0),
       'e': (0, 1),
       's': (1, 0),
       'w': (0, -1),
       'halt': (0,0),
       None: (0,0)}

class RewardEvents:
    def __init__(self):
        self.food_eaten = 0
        self.death_dealt = 0
        self.was_killed = False

class AntStatus:
    '''Enum type to represent persistent ant status.'''
    UNKNOWN = 0
    ALIVE = 1
    DEAD = 2
    ToString = ("UNKNOWN", "ALIVE", "DEAD")

class Ant(object):
    '''The persisent Ant class. It stores a location, direction, persistent id number for identification, and status. By setting the direction, the AntsWorld will automatically execute the corresponding orders at the end of the turn.'''
    def __init__(self, world, pos, ant_id):
        self.ant_id = ant_id
        self.location = pos    
        self.direction = None
        self.status = AntStatus.ALIVE
        self.world = world

    def __str__(self):
        return ("<[%s]%d:(%s)->%s>" % (AntStatus.ToString[self.status], self.ant_id, str(self.location), self.direction))

    ############################################################################
    ## These methods to be deprecated...
    ############################################################################
        
    def distance(self, targ): 
        '''Get the distance to a target location.'''
        return self.world.distance(self.location, targ)

    def sort_by_distance(self, targ_list): 
        '''Returns a sorted list (dist, (x,y)) from an initial list of (x,y) positions, sorted in ascending order of distance to this ant.'''
        return self.world.sort_by_distance(self.location, targ_list)

    def toward(self, targ):
        """Get the possible directions that move this ant closer to this target. Since ants can't move diagonally, there may be multiple directions."""
        return self.world.toward(self.location, targ)
        
    def closest_food(self):
        '''Get the closest food, or None if no food is in sight.'''
        return self.world.closest_food(self.location)

    def closest_enemy(self):
        '''Get the closest enemy, or None if no enemy is in sight.'''
        return self.world.closest_enemy(self.location)

    def get_passable_direction(self, dirs):
        """Filter a list of NSEW directions to remove directions that are not passable from an ant's current position. Returns the FIRST direction that is passable."""
        return self.world.get_passable_direction(self.location, dirs)

class AntWorld(object):
    '''The AntWorld class. No AntsBot should ever be without one.'''
    def __init__(self, engine=None):

        # Useful game state parameters.
        self.width = None
        self.height = None
        self.map = None
        
        # Lookup tables for enemies, friendly ants, and food.
        self.enemy_dict = {}
        self.food = []
        self.dead_dict = {}
        self.ant_lookup = {}
        self.ants = []

        # Default logger is the global logger (see logutil.py).
        self.L = L
        self.engine = engine
        
        self.stateless = False
        self.debug_mode = False

    def _setup_parameters(self, data):
        '''Parse raw data to determine game settings.'''
        for line in data.split('\n'):
            line = line.strip().lower()
            if len(line) > 0:
                tokens = line.split()

                if self.debug_mode:
                    self.L.debug("tokens: " + str(tokens))

                key = tokens[0]
                if key == 'cols':
                    self.width = int(tokens[1])
                elif key == 'rows':
                    self.height = int(tokens[1])
                elif key == 'player_seed':
                    random.seed(int(tokens[1]))
                elif key == 'turntime':
                    self.turntime = int(tokens[1])
                elif key == 'loadtime':
                    self.loadtime = int(tokens[1])
                elif key == 'viewradius2':
                    self.viewradius2 = int(tokens[1])
                elif key == 'attackradius2':
                    self.attackradius2 = int(tokens[1])
                elif key == 'spawnradius2':
                    self.spawnradius2 = int(tokens[1])

        # Initialize all land map.
        self.map = [[LAND for col in range(self.width)]
                                for row in range(self.height)]
            
        # Initialize ant tracker state to no ants.
        for i in range(self.height):
            for j in range(self.width):
                self.ant_lookup[(i,j)] = -1
        self.L.debug("World state initialized")

    # _updates a world state based on data from the engine/server.
    def _update(self, data, engine_ants):
        if self.debug_mode:
            self.L.debug("Updating world state:")

        # Clear map of last turn's friendly ants.
        for row, col in [ant.location for ant in self.ants]:
            self.map[row][col] = LAND

        # Clear map of last turn's enemy ants, food, and bodies.
        clear_these = (self.food + self.enemy_dict.keys() + self.dead_dict.keys())
        if len(clear_these) > 0:
            for row, col in clear_these:
                self.map[row][col] = LAND

        # Reset food, enemy, and dead body locations.
        self.food = []
        self.enemy_dict = {}
        self.dead_dict = {}

        # This dictionary will store a list of friendly ants communicated
        # by the server; if an ant doesn't show up on this list, then it
        # should be dead, otherwise we have no idea what happened to it.
        check_ants = {}

        if self.stateless:
            self.ants = []
        
        # Now parse the data.
        for line in data.split('\n'):
            line = line.strip().lower()
            if len(line) > 0:
                tokens = line.split()

                # Only lines with more than 3 tokens are valid messages.
                if len(tokens) >= 3:
                    row = int(tokens[1])
                    col = int(tokens[2])
                    if tokens[0] == 'a': # ant found

                        # _update map with owner of ant.
                        owner = int(tokens[3])
                        self.map[row][col] = owner

                        # Update internal lookup dictionaries.
                        if owner == MY_ANT:
                            if self.stateless:
                                pos = (row, col)
                                ant_id = len(self.ants)
                                if self.debug_mode:
                                    self.L.debug("New ant %d found at (%d,%d)" % (ant_id, pos[0], pos[1]))
                                self.ants.append(Ant(self, pos, ant_id))
                                self.ant_lookup[pos] = ant_id
                            else:
                                if self.debug_mode:
                                    self.L.debug("RCV MY ANT at %s" % str((row,col)))
                                check_ants[(row, col)] = owner
                        else:
                            self.enemy_dict[(row, col)] = owner

                    elif tokens[0] == 'f': # food found
                        self.map[row][col] = FOOD
                        self.food.append((row, col))
                    elif tokens[0] == 'w': # water found
                        self.map[row][col] = WATER
                        if self.debug_mode:
                            self.L.debug("RCV WATER at %d,%d" % (row,col))
                    elif tokens[0] == 'd': # dead body found
                        self.map[row][col] = DEAD
                        self.dead_dict[(row,col)] = True
        
        if not self.stateless:
            self._track_friendlies(check_ants)
            self._join_with_engine_ants(engine_ants)
            
#            for a in self.ants:
#                self.L.debug("\nAnt #%d ---------------" % a.ant_id)
#                self.L.debug('died = %d' % a.died)
#                self.L.debug('food_amt = %s' % str(a.food_amt))
#                self.L.debug('kill_amt = %s' % str(a.kill_amt))
#                self.L.debug('location = %s' % str(a.location))
#                self.L.debug('direction = %s' % a.direction)
        
        
    def _join_with_engine_ants(self,engine_ants):
        loc2id = {}        
        for ant in self.ants:
            loc2id[ant.location] = ant.ant_id
            
        # sanity check: make sure there is a one-to-one mapping of check_ants and engine_ants
        claimed_spots = {}
        for i,engine_ant in zip(range(len(engine_ants)),engine_ants):
            if engine_ant.loc not in loc2id:
                self.L.error("Engine thinks ant at %s, but worldstate has no such ant!" % str(engine_ant.loc))
            elif engine_ant.loc in claimed_spots:
                self.L.error("Engine thinks 2 ants in spot %s: %d and %d!" % (str(engine_ant.loc),claimed_spots[engine_ant.loc],i))
            else:
                claimed_spots[engine_ant.loc] = i
                
                
        # if everything is ok, copy over synced info for learning
        for engine_ant in engine_ants:
            ant = self.ants[loc2id[engine_ant.loc]]
            ant.previous_reward_events = RewardEvents()
            ant.previous_reward_events.food_eaten = engine_ant.food_amt
            ant.previous_reward_events.death_dealt = engine_ant.kill_amt
            ant.previous_reward_events.was_killed = (ant.status == AntStatus.DEAD)
                        
             
                
        
                

    def _track_friendlies(self, check_ants):
        # Track friendly living ants.
        for ant in [a for a in self.ants 
                                if a.status == AntStatus.ALIVE]:                                    
            if self.debug_mode:
                self.L.debug("tracking ant: %d - %s" % (ant.ant_id, str(ant.location)))

            # Ant stats is unknown until proven otherwise.
            ant.status = AntStatus.UNKNOWN

            # Remove ant's last location from tracker dict.
            self.ant_lookup[ant.location] = -1
        
            # Look at where we project the ant to be based on last
            # turn's direction.
            next_pos = ant.location
            if ant.direction != None:
                proj_pos = self.next_position(ant.location, ant.direction)
                if self.debug_mode:
                    self.L.debug("projected position: %s --> %s" % 
                                 (ant.direction, str(proj_pos)))

                # Note: if the ordered direction was not passable, it will not
                # have moved.
                if self.passable(proj_pos):
                    next_pos = proj_pos
                else:
                    if self.debug_mode:
                        self.L.debug("projection NOT passable")

            # Look for the live ant in the list received from the server.
            if check_ants.has_key(next_pos):
                if self.debug_mode:
                    self.L.debug("FOUND ant %d at %s" % (ant.ant_id, str(next_pos)))

                # Update living ant's position and status.
                ant.status = AntStatus.ALIVE
                ant.location = next_pos
                self.ant_lookup[next_pos] = ant.ant_id
                check_ants.pop(next_pos)
            elif self.dead_dict.has_key(next_pos):

                # Ant is dead :(
                if self.debug_mode:
                    self.L.debug("FOUND ant %d DEAD at %s" % (ant.ant_id, str(next_pos)))
                ant.status = AntStatus.DEAD
            else:

                # We didn't find a body or the ant.
                self.L.error("MISSING ant %d at %s: %s" %
                                (ant.ant_id, str(next_pos), 
                                  str(self.map[next_pos[0]][next_pos[1]])))

        # Add any remaining ants that weren't known previously.
        for pos in check_ants.keys():
            if self.ant_lookup[pos] != -1:
                self.L.error("Duplicate ant found at (%d,%d)" %
                                  (pos[0], pos[1]))
            else:
                ant_id = len(self.ants)
                if self.debug_mode:
                    self.L.debug("New ant %d found at (%d,%d)" % 
                                 (ant_id, pos[0], pos[1]))
                self.ants.append(Ant(self, pos, ant_id))
                self.ant_lookup[pos] = ant_id

        # Print out a status to the log window. First dead ants, then
        # unknown, and then alive.
        if self.debug_mode:
            for ant in [a for a in self.ants 
                                    if a.status == AntStatus.DEAD]:
                self.L.debug("ant %d status: %s, %s" % 
                                (ant.ant_id, str(ant.location),
                                AntStatus.ToString[ant.status]))
            for ant in [a for a in self.ants 
                                    if a.status == AntStatus.UNKNOWN]:
                self.L.warning("ant %d status: %s, %s" % 
                                (ant.ant_id, str(ant.location),
                                AntStatus.ToString[ant.status]))
            for ant in [a for a in self.ants 
                                    if a.status == AntStatus.ALIVE]:
                self.L.info("ant %d status: %s, %s" % 
                                (ant.ant_id, str(ant.location),
                                AntStatus.ToString[ant.status]))

    def _finish_turn(self):
        '''Finish the turn by sending out the orders to the game engine or server.'''

        # Check for invalid direction.
        for a in self.ants:
            if a.direction != None and a.direction not in  AIM.keys():
                raise AssertionError("%s is not a valid direction!" % a.direction)
            
        # Only send orders for alive, moving ants.
        orders = ['o %d %d %s' % 
                            (a.location[0], a.location[1], a.direction)
                            for a in self.ants if a.direction != None and
                            a.status == AntStatus.ALIVE]

        if self.engine == None: # Should send to stdout
            msg = '\n'.join(orders) + '\ngo\n'
            sys.stdout.write(msg)
            sys.stdout.flush()
            return "wrote to stdout"
        else:
            return orders # No 'go' is necessary here

    @property
    def enemies(self):
        return self.enemy_dict.keys()

    def passable(self, loc):
        return self.map[loc[0]][loc[1]] > WATER
    
    def unoccupied(self, loc):
        row,col = loc
        return self.map[row][col] in (LAND, DEAD)

    def next_position(self, location, direction):
        '''Get the next position occupied by an ant moving in a specific direction. (Sphere world makes this non-trivial).'''
        row, col = location
        d_row, d_col = AIM[direction]
        return ((row + d_row) % self.height, (col + d_col) % self.width)

    def manhattan_distance(self,loc1,loc2):
        '''Grid distance between two locations on sphere world.'''
        row1,col1 = loc1
        row2,col2 = loc2
        if (row1 > self.height):
            row1 = row1 - self.height
        if (row2 > self.height):
            row2 = row2 - self.height 
        if (col1 > self.width):
            col1 = col1 - self.width
        if (col2 > self.width):
            col2 = col2 - self.width
        
        #row1 = row1 % self.height
        #row2 = row2 % self.height
        #col1 = col1 % self.width
        #col2 = col2 % self.width
        if col2 > col1:
            d_col = col2 - col1
        else:
            d_col = col1 - col2            
        if d_col > self.width/2:
            d_col = self.width - d_col

        if row2 > row1:
            d_row = row2 - row1
        else:
            d_row = row1 - row2            
        if d_row > self.height/2:
            d_row = self.height - d_row

        #d_col = min(abs(col1 - col2), self.width - abs(col1 - col2))
        #d_row = min(abs(row1 - row2), self.height - abs(row1 - row2))
        return d_row + d_col
    
    def euclidean_distance2(self,x,y):
        ''' Euclidean distance between x and y squared '''
        d_row = abs(x[0] - y[0])
        d_row = min(d_row, self.height - d_row)
        d_col = abs(x[1] - y[1])
        d_col = min(d_col, self.width - d_col)
        return d_row**2 + d_col**2
        
    def distance(self, loc1, loc2):
        """Distance between two locations on sphere world.
        I don't like the ambiguous naming, but for backwards compatibility, keeping this"""
        return self.manhattan_distance(loc1,loc2)

    def sort_by_distance(self, loc, targ_list): 
        '''Returns a sorted list (dist, (x,y)) from an initial list of (x,y) positions, sorted in ascending order of distance to this ant.'''
        dists = [ (self.distance(loc, targ), targ) 
                            for targ in targ_list ]

        dists.sort(key=(lambda x: x[0]))
        return dists

    def toward(self, loc, targ):
        """Get the possible directions that move this ant closer to this target. Since ants can't move diagonally, there may be multiple directions."""
        if targ is None:
            return []
        else:
            return self.directions(loc, targ)

    def closest_food(self, loc):
        '''Get the closest food, or None if no food is in sight.'''
        dists = self.sort_by_distance(loc, self.food)
        if dists:
            return dists[0][1]
        else:
            return None

    def closest_enemy(self, loc):
        '''Get the closest enemy, or None if no enemy is in sight.'''
        dists = self.sort_by_distance(loc, self.enemies)
        if dists:
            return dists[0][1]
        else:
            return None

    def closest_friend(self, loc):
        """Get the closest friendly ant to this position that is not on this position"""
        ant_locs = [ant.location for ant in self.ants]
        dists = self.sort_by_distance(loc, ant_locs)
        if dists:
            if dists[0][1] == loc:
                if len(dists) > 1:
                    return dists[1][1]
                else:
                    return None
            else:
                return dists[0][1]
        else:
            return None

    def get_passable_direction(self, loc, dirs):
        """Filter a list of NSEW directions to remove directions that are not passable from an ant's current position. Returns the FIRST direction that is passable."""
        if dirs is None:
            return None
        for d in dirs:
            l = self.next_position(loc, d)
            if self.passable(l) and self.unoccupied(l):
                return d
        return None
    
    def get_passable_directions(self, loc, dirs):
        """Filter a list of NSEW directions to remove directions that are not passable from an ant's current position. Returns the FIRST direction that is passable."""
        if dirs is None:
            return None
        passable_dirs = list()
        for d in dirs:
            l = self.next_position(loc, d)
            if self.passable(l) and self.unoccupied(l):
                passable_dirs.append(d)
        return passable_dirs

    def directions(self, loc1, loc2):
        '''Get directions that move closer to loc2 from loc1.
        
        This horrible function was copied from the distribution code.'''
        
        if loc1 == loc2:
            return [None]
        
        d = []
        row1, col1 = loc1
        row2, col2 = loc2

        row1 = row1 % self.height
        row2 = row2 % self.height
        col1 = col1 % self.width
        col2 = col2 % self.width
        if row1 < row2:
            if row2 - row1 >= self.height//2:
                d.append('n')
            if row2 - row1 <= self.height//2:
                    d.append('s')
        if row2 < row1:
            if row1 - row2 >= self.height//2:
                d.append('s')
            if row1 - row2 <= self.height//2:
                d.append('n')
        if col1 < col2:
            if col2 - col1 >= self.width//2:
                d.append('w')
            if col2 - col1 <= self.width//2:
                d.append('e')
        if col2 < col1:
            if col1 - col2 >= self.width//2:
                d.append('e')
            if col1 - col2 <= self.width//2:
                d.append('w')

        return d
    
    def _render_text_map(self, map=None):
        tmp = ''
        if map == None:
            map = self.map
        for row in map:
            tmp += '# %s\n' % ''.join([MAP_RENDER[col] for col in row])
        return tmp

