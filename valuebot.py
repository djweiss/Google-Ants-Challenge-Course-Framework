#!/usr/bin/env python
# Created: October 2011
# Author: David Weiss
import random
import json
import os.path

from src.antsbot import AntsBot
from src.worldstate import AIM, AntStatus
from src.mapgen import SymmetricMap
from src.features import FeatureExtractor, BasicFeatures
from src.state import GlobalState
               
class ValueBot(AntsBot):
    """ Value function based AntsBot.

    This is a template class that uses a FeatureExtractor and a set of weights to make decisions
    based on a weighted sum of features (value function.) It is capable of loading and saving to JSON using
    the FeatureExtractor.to_dict() method and FeatureExtractor(input_dict) constructor.
      
    """
    
    def __init__(self, world, load_file="valuebot.json"):
        """Initialize, optionally loading from file. 
        
        Note: this bot disables tracking of friendly ants in the AntWorld, 
        so that ant_id is no longer consistent between turns. This speeds up
        game speed dramatically, but means it is trickier to maintain specific ant states.
        """
        
        AntsBot.__init__(self, world)
        self.state = None
        self.features = None
        self.weights = None
        
        # **** NOTE: Disable ant tracking to speed up game playing. 
        self.world.stateless = False
        
        # Try to load saved configuration from file
        if load_file is not None and os.path.exists(load_file):
            fp = file(load_file, "r")
            data = json.load(fp)
            self.set_features(FeatureExtractor(data['features']))
            self.set_weights(data['weights'])
            fp.close()
    
    def save(self, filename):
        """Save features and weights to file."""
        
        fp = file(filename, "w")
        data = {'features': self.features.to_dict(), 
                'weights': self.weights }
        json.dump(data, fp)
        fp.close()
        
        
    def save_readable(self, filename):
        """Save features and weights to file."""
        
        fp = file(filename, "w")
        fp.write(str(self))
        0
        
        fp.close()
            
    def __str__(self):
        """Print a labeled list of weight values."""
        
        s = 'ValueBot:\n'
        for i in range(self.features.num_features()):
            s += '\t%s = %g\n' % (self.features.feature_name(i), 
                                  self.weights[i])
        return s
    
    def set_features(self, extractor):
        self.features = extractor
        self.world.L.debug("Setting features: %s" % str(self.features))
        
    def set_weights(self, weights):
        """Set weight vector. Note: checks that len(weights) == self.features.num_features()."""                    
                
        self.weights = weights
        self.world.L.debug("Setting weights: %s" % str(self.weights))
        if self.features == None or not len(self.weights) == self.features.num_features():
            raise AssertionError("Features need to be set before weights!")

    def value(self, state, loc, action):
        """Compute the value of a given action w.r.t. a given state and ant location."""
        
        feature_vector = self.features.extract(self.world, state, loc, action)
        
#        self.world.L.info("Evaluating move: %s, %s:" % (str(loc), action))
        dot_product = 0
        for i in range(0, len(feature_vector)):
            if feature_vector[i]:
#                self.world.L.info("\tf: %s = %g" % (self.features.feature_name(i), self.weights[i]))
                dot_product += self.weights[i]
#        self.world.L.info("\tdot_product = %g" % dot_product)
        
        return dot_product
             
    def get_direction(self, ant):
        """Evaluates each of the currently passable directions and picks the one with maximum value."""
        
        # get the passable directions, in random order to break ties
        rand_dirs = self.world.get_passable_directions(ant.location, AIM.keys())
        random.shuffle(rand_dirs)
        
        # evaluate the value function for each possible direction
        value = [0 for i in range(0, len(rand_dirs))]
        max_value = float("-inf")
        max_dir = None
        for i in range(0, len(rand_dirs)):
            value[i] = self.value(self.state, ant.location, rand_dirs[i])
            if value[i] > max_value:
                max_value = value[i]
                max_dir = rand_dirs[i]
                
        # take direction with maximum value
        # Get the first passable direction from that long list.
        self.world.L.info("Chose: %s, value: %.2f" % (max_dir, max_value))
        return max_dir

    # Main logic
    def do_turn(self):
        """Precomputes global state, and then chooses max value action for each ant independently."""
        
        # Run the routine for each living ant independently.
        next_locations = {}
        
        # Grid lookup resolution: size 10 squares
        if self.state == None:
            self.state = GlobalState(self.world, resolution=10)
        else:
            self.state.update()
        
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

    def reset(self):
        self.state = None
        
# Set BOT variable to be compatible with rungame.py                            
BOT = ValueBot

if __name__ == '__main__':
    from src.localengine import LocalEngine
    from greedybot import GreedyBot
    import sys
    
    engine = LocalEngine()

    # Load the bot from file
    engine.AddBot(ValueBot(engine.GetWorld(), load_file="saved_bots/qbot.json"))
        
    # Add a GreedyBot opponent    
    engine.AddBot(GreedyBot(engine.GetWorld()))

    # Generate and play on random 30 x 30 map
    random_map = SymmetricMap(min_dim=30, max_dim=30)
    random_map.random_walk_map()
    fp = file("src/maps/2player/my_random.map", "w")
    fp.write(random_map.map_text())
    fp.close()
    
    # Run the local debugger
    engine.Run('play',sys.argv + ["--run", "-m", "src/maps/2player/my_random.map"])

    
