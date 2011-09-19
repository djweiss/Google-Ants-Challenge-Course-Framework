#!/usr/bin/env python
# Created: July 2011
# Author: Ben Sapp
#
# A bot designed to guide a single ant from a start location to a food location
# in a static, fully observable environment.

import sys
from antsbot import AntsBot
from localengine import LocalEngine
from optparse import OptionParser
import antpathsearch

class MazeBot(AntsBot):
    ''' A simple bot which gets from a spawn state to a single food location using path planning algorithms. '''

    def __init__(self,world,path_planner):
        AntsBot.__init__(self,world)
        self.path_planner = path_planner
        
    # Main logic
    def do_turn(self):
        ''' 
        Step 0: plan a path to the closest food.
        Steps 1 through n: carry out the plan
        Step n+1: ???
        Step n+2: profit
        '''
        ant = self.world.ants[0]
        
        # figure out how to get to the food
        if self.world.engine.turn == 1:
            self.curr_step = 0
            self.food_path = self.path_planner.get_path(ant.location,ant.closest_food())
            
        
        # once we have a food path, we know exactly what to do
        next_loc = self.food_path[self.curr_step+1]
        ant.direction = self.world.directions(ant.location,next_loc)
        ant.direction = ant.direction[0]
        self.curr_step += 1
                     
                
if __name__ == '__main__':

    # From Ants distribution: use pyco to speed up all code.
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass
    
        parser = OptionParser()
        parser.add_option("-m", "--map_file", dest="map",default='maps/1player/open.map',
                      help="Name of the map file")
        parser.add_option("--step-through", dest="step_through", default=True, type="int",
                        help="Hit enter to step through turns")
        parser.add_option("-p", "--planner", dest="planner",default='bfs',
                      help="Type of path planner, one of {dfs,bfs,astar}")
        
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
        world = engine.GetWorld()

        planner = {}
        planner['bfs'] = antpathsearch.BreadthFirstSearch(world)
        planner['dfs'] = antpathsearch.DepthFirstSearch(world)
        planner['astar'] = antpathsearch.aStarSearch(world)

        my_planner = planner[opts.planner]
        engine.AddBot(MazeBot(world,my_planner))
        engine.Run(engineopts)
      
           
