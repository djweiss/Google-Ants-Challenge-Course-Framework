#!/usr/bin/env python
# Created: September 2011
# Author: Jennifer Gillenwater
#
# An example deterministic finite automaton (DFA) bot.

import sys
import time
from antsbot import AntsBot
from greedybot import GreedyBot
from worldstate import AIM, AntStatus, AntWorld

class ExploreDFA:
    '''A DFA that tends to encourage an ant to explore unvisited locations.'''
    
    def new_state(self, ant):
        '''Marks the current ant location as visited once.'''
        state = {}
        state[ant.location] = 1
        return state

    def get_direction(self, state, ant):
        '''Returns the ant's least-visited adjacent location, prioritizing by
           food direction when multiple adjacent locations are equally explored.''' 
        # Of the 4 possible squares to move to, determine which don't currently
        # contain an ant and are the least-visited.
        min_visits = float('Inf')
        min_visits_directions = []
        for direction in AIM.keys():
            test_position = ant.world.next_position(ant.location, direction)
            
            # Ignore water.
            if not ant.world.passable(test_position):
                continue
            
            # Don't move to a currently occupied location;
            # this helps somewhat mitigate collisions.
            if ant.world.ant_lookup[test_position] != -1:
                continue
            
            # Check to see how frequently this candidate location has been visited
            # in the past.
            num_visits = state[test_position] if state.has_key(test_position) else 1
            if num_visits < min_visits:
                min_visits = num_visits
                min_visits_directions = [direction]
            elif num_visits == min_visits:
                min_visits_directions.append(direction)

        if not min_visits_directions:
            # Will only reach here if ant is boxed in by water on all sides.
            return None
        elif len(min_visits_directions) > 1:
            # Try to break ties by considering food direction.
            food_directions = ant.toward(ant.closest_food())
            for fd in food_directions:
                if fd in min_visits_directions:
                    return fd

        return min_visits_directions[0]
        
    def update_state(self, state, ant):
        if state.has_key(ant.location):
            state[ant.location] += 1
        else:
            state[ant.location] = 1

class DFABot(AntsBot):
    def __init__(self, world):
        self.world = world
        self.dfa = ExploreDFA()
        self.ant_state = {}
    
    # Main logic
    def do_turn(self):
        # Run the routine for each living ant independently.
        for ant in self.world.ants:
            if ant.status == AntStatus.ALIVE:
                if ant.ant_id in self.ant_state:
                    state = self.ant_state[ant.ant_id]
                else:
                    state = self.dfa.new_state(ant)
                    self.ant_state[ant.ant_id] = state
                direction = self.dfa.get_direction(state, ant)
                self.dfa.update_state(state, ant)
                ant.direction = direction
                

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
            from batchlocalengine import BatchLocalEngine
            from mapgen import SymmetricMap

            engine = BatchLocalEngine()
            engine.AddBot(GreedyBot(engine.GetWorld()))
            engine.AddBot(GreedyBot(engine.GetWorld()))
            engine.PrepareGame(sys.argv)
            engine.game.efficient_update = True
            
            num_games = 10
            # Run 100 random games.
            start_time = time.time()
            for i in range(0, num_games):
                random_map = SymmetricMap(min_dim=60, max_dim=60)
                random_map.random_walk_map()                
                engine.game.Reset(random_map.map_text())
                engine.Run()
                print [float(r) for r in engine.game.score], "turn", engine.turn
            elapsed = time.time() - start_time
            sum_bots = 0
            print "Time summary: %.2f s total elapsed = %.2f s/game " % (elapsed, elapsed/num_games)
            for b,bot in engine.bots:
                sum_bots += engine.bot_time[b]
                print "\tbot %d %s: %.5f s = %.2f%%" % (b, str(bot.__class__), engine.bot_time[b], engine.bot_time[b]/elapsed*100)     
            print "\tengine: %.5f s = %.2f%%" % (elapsed-sum_bots, (elapsed-sum_bots)/elapsed*100)
            
        else: # Run as stand-alone process
            bot = DFABot(AntWorld())
            bot._run()

    except KeyboardInterrupt:
        print('ctrl-c, leaving ...')
