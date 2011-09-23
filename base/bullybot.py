#!/usr/bin/env python
# Created: July 2011
# Author: Ben Sapp
#
# A mean bot who coordinates multiple ants to go kill a single enemy ant
# using A*


import sys
import math
from worldstate import AIM
from antsbot import AntsBot
from localengine import LocalEngine
from stillbot import StillBot
from Queue import PriorityQueue
import hungarian

class BullyBot(AntsBot):

    def __init__(self,world):
        AntsBot.__init__(self,world)
        
        
    # Main logic
    def do_turn(self):
        self.attackradius = math.sqrt(self.world.attackradius2)
        
        antlocs = [ant.location for ant in self.world.ants] 
        # figure out how to get to the food
        if self.world.engine.turn == 1:
            self.curr_step = 0
            enemy = self.world.ants[0].closest_enemy()
            self.path = self.aStar_multi(antlocs, enemy)
        
        # once we have a path, we know exactly what to do
        nextlocs = self.path[self.curr_step+1]
        dirs = self.locations_to_directions(antlocs,nextlocs)
        for ant,dir in zip(self.world.ants,dirs):
            ant.direction = dir
        self.curr_step += 1
        
    def get_successors_one_ant(self,loc):
        world = self.world
        # possible directions an ant can move
        alldirs = AIM.keys()
        
        #important: add in the option to stay put, this allows ants to sit and
        #wait for other ants to catch up so they can attack together
        s = [loc]
        for d in alldirs:
            l = world.next_position(loc, d)
            if world.passable(l):
                s.append(l)
        return s

    def get_successors(self,currlocs, enemy):
        '''
        YOUR CODE HERE
        Return reachable next states from current locations. Be sure to avoid
        duplicate states, and states where an ant gets too close to the enemy
        before it is time to attack.  You should use get_successors_one_ant as
        part of your code.
        '''
        world = self.world
        return [(0,0),(0,0)]

    
    def ants_in_enemy_range(self,locs,enemy):
        '''
        Returns a boolean vector for each location if the locations are in attack range of the enemy.
        Might be helpful.
        '''
        return [self.world.engine.game.distance(loc,enemy) < self.world.attackradius2 for loc in locs]
    
    def is_goal_state(self,world,locs,enemy):
        '''
        If any of the ants is too far from the enemy, we're not there yet 
        '''
        return all(self.ants_in_enemy_range(locs,enemy))        
        
        
        
    def heuristic_cost(self,world,locs,enemy):
        '''
        YOUR CODE HERE
        Write an admissable but non-trivial heuristic 
        '''
        return 0 
                        
    def aStar_multi(self,antlocs,enemy_ant):
        '''
        YOUR CODE HERE 
        Implement or reuse code to solve the multi-ant search
        problem here.  Should return a list of tuples of ant location 2-tuples, as demonstrated
        by the dummy PATHS variable below.
        '''
           
        start = tuple(antlocs)
        goal = enemy_ant
        world = self.world
        
        q = PriorityQueue()
        
        # a fake set of paths for the ants, consisting of 10 steps
        paths = []
        for i in range(10):
            paths.append(start)

        return paths
      
    
    def locations_to_directions(self,currlocs,nextlocs):
        '''
        Matches up currlocs so that by taking the next directions, nextlocs will be covered.  
        There are possibly many solutions; this finds one using the hungarian algorithm
        '''
        
        # setup a bipartite graph with an edge between location A in currlocs and
        # location B in nextlocs iff B is reachable from A in one move
        
        if len(currlocs) != len(nextlocs):
            print 'number of current locations not equal to number of next locations'
            raise
        
        W = []
        for loc in currlocs:
            successors = self.get_successors_one_ant(loc)
            w = []
            for next in nextlocs:
                w.append(next in successors)
            W.append(w)
        
        # hungarian algorithm finds a one-to-one matching from a bipartite graph
        u2v = hungarian.maxWeightMatching(W)[0]
        dirs = []
        for i in range(len(u2v)):
            dirs.append(self.world.directions(currlocs[i],nextlocs[u2v[i]])[0])
            
        return dirs
    
if __name__ == '__main__':

    # From Ants distribution: use pyco to speed up all code.
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass

   
    parser = OptionParser()
    parser.add_option("-m", "--map_file", dest="map",default='maps/bully/open.map',
                  help="Name of the map file")
    parser.add_option("--step-through", dest="step_through", default=True, type="int",
                    help="Hit enter to step through turns")
    
    (opts, args) = parser.parse_args(sys.argv)
    # Don't mess with these options, because these are what the testing code will use
    engineopts = ['--run']
    engineopts.append('-t 99999')
    engineopts.append('--viewradius2=99999')
    engineopts.append('--food=none')
    engineopts.append('--turntime=1000')
    engineopts.append('--step-through=%d' % opts.step_through)
    engineopts.append('--map_file=%s' % opts.map)

    engine = LocalEngine()
    engine.AddBot(BullyBot(engine.GetWorld()))
    engine.AddBot(StillBot(engine.GetWorld()))
    engine.Run(engineopts)

