#!/usr/bin/env python
# Created: September 2011
# Author: Jennifer Gillenwater
#
# An example deterministic finite automaton (DFA) bot.

from src.antsbot import AntsBot
from src.worldstate import AIM, AntStatus, AntWorld

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

BOT = DFABot
