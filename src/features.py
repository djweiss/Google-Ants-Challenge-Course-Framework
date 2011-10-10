'''
Created on Oct 1, 2011

@author: djweiss
'''

class FeatureExtractor:
    ''' Extracts features from ant world state for given actions.
    
    This is the template class for all feature extractors. 
    A feature extractor must implement the init_from_dict() and extract() methods.  
    '''
    
    def __init__(self, input_dict):
        ''' Create a new FeatureExtractor from a dict object.'''
        
        new_type = input_dict['_type']
        if new_type == MovingTowardsFeatures.type_name: 
            self.__class__ = MovingTowardsFeatures
        elif new_type == QualifyingFeatures.type_name:
            self.__class__ = QualifyingFeatures
        elif new_type == CompositingFeatures.type_name:
            self.__class__ = CompositingFeatures 
        else:
            raise Exception("Invalid feature class %s" + new_type)

        self.feature_names = []
        self.feature_id = {}
        
        # Call class-specific initialization.    
        self.init_from_dict(input_dict)
        
        fid = 0
        for name in self.feature_names:
            self.feature_id[name] = fid
            fid += 1

    def __str__(self):
        return str(self.__class__)
        
    def to_dict(self):
        """Convert FeatureExtractor to a human readable dict."""
        
        return {'_type': self.__class__.type_name}

    def num_features(self):
        """Size of feature vector output by this extractor."""
        
        return len(self.feature_names)
    
    def feature_name(self, fid):
        """Get the name of the fid'th feature as a string.""" 
        
        return self.feature_names[fid]
    
    def feature_id(self, name):
        """Reverse lookup the feature id of the specified feature name."""
        
        return self.feature_id[name]
       
    def init_from_dict(self, input_dict):
        """Perform any class-specific initialization, grabbing parameters from input_dict.""" 
        raise NotImplementedError
        
    def extract(self, world, state, loc, action):
        """Extracts a feature vector from a world, state, location, and action. 
        
        Feature vectors are lists of booleans, where length = num_features() regardless of 
        the # of active features.
        """
        
        raise NotImplementedError

class MovingTowardsFeatures(FeatureExtractor):
    """Very basic features.
    
    Computes three features: whether or not a given action takes an ant nearer to its closest
    enemy, food, or friendly ant.
    """
    
    type_name = 'MovingTowards'
       
    def init_from_dict(self, input_dict):
        self.feature_names.append("Moving Towards Closest Enemy")
        self.feature_names.append("Moving Towards Closest Food")
        self.feature_names.append("Moving Towards Friendly")

    def __init__(self):
        FeatureExtractor.__init__(self, {'_type': MovingTowardsFeatures.type_name})    
                
    def moving_towards(self, world, loc1, loc2, target):
        """Returns true if loc2 is closer to target than loc1 in manhattan distance."""
        
        return world.manhattan_distance(loc1, target) - world.manhattan_distance(loc2, target) > 0

    def find_closest(self, world, loc, points):
        """Returns the closest point to loc from the list points, or None if points is empty."""
        if len(points) == 1:
            return points[0]
        
        locs = world.sort_by_distance(loc, points)
            
        if len(locs) > 0:
            return locs[0][1]
        else:
            return None
        
    def extract(self, world, state, loc, action):
        """Extract the three simple features."""
        
        food_loc = self.find_closest(world, loc, state.lookup_nearby_food(loc))
        enemy_loc = self.find_closest(world, loc, state.lookup_nearby_enemy(loc))
        friend_loc = self.find_closest(world, loc, state.lookup_nearby_friendly(loc))

        next_loc = world.next_position(loc, action)
        world.L.debug("loc: %s, food_loc: %s, enemy_loc: %s, friendly_loc: %s" % (str(loc), str(food_loc), str(enemy_loc), str(friend_loc)))
        # Feature vector        
        f = list()
        
        # Moving towards enemy
        if enemy_loc is None:
            f.append(False)
        else:
            f.append(self.moving_towards(world, loc, next_loc, enemy_loc));
        
        # Moving towards food
        if food_loc is None:
            f.append(False)
        else:
            f.append(self.moving_towards(world, loc, next_loc, food_loc));
        
        # Moving towards friendly
        if friend_loc is None:
            f.append(False)
        else:
            f.append(self.moving_towards(world, loc, next_loc, friend_loc));
        
        return f
    
class QualifyingFeatures(FeatureExtractor):
    """Additional qualifier-type features.
    
    This is part of the assignment for HW3. Your features in this class don't have to depend on
    the action, but instead can be functions of state or location, e.g., "1 ant left".
    
    """
    
    type_name = 'Qualifying'    
    
    def __init__(self):
        pass
        
    def init_from_dict(self, input_dict):
        raise NotImplementedError
    
    def extract(self, world, state, loc, action):
        raise NotImplementedError

class CompositingFeatures(FeatureExtractor):
    """Generates new features from new existing FeatureExtractors.
    
    This is part of the assignment for HW3. CompositingFeatures takes two FeatureExtractors,
    base_f and qual_f. If len(base_f) = n and len(qual_f) = m, then this extractor generates 
    n(m+1) features consisting of the original base_f features plus a copy of base_f features 
    that is multiplied by each of the qual_f features.
    
    It is important to compute the unique names of each feature to help with debugging.

    """
    
    type_name = 'Compositing'        

    def __init__(self, base_f, qual_f):
        FeatureExtractor.__init__(self, {'_type': CompositingFeatures.type_name, 
                                         'base_f' : base_f.to_dict(), 'qual_f': qual_f.to_dict()})
                             
    def init_from_dict(self, input_dict):
        self.base_f = FeatureExtractor(input_dict['base_f']) 
        self.qual_f = FeatureExtractor(input_dict['qual_f']) 

        # Compute names based on the features we've loaded    
        self.compute_feature_names()

    def to_dict(self):
        val =  FeatureExtractor.to_dict(self)
        val['base_f'] = self.base_f.to_dict()
        val['qual_f'] = self.qual_f.to_dict()
        return val
        
    def compute_feature_names(self):
        """ Compute the list of feature names from the composition of base_f and qual_f. The
        features should be organized as follows. If base_f has n features and qual_f has m features,
        then the features are indexed as follows:
        
        f[0] through f[n-1]: base_f[0] through base_f[n-1]
        f[n] through f[2n-1]: base_f[0]*qual_f[0] through base_f[n]*qual_f[0] 
        ...
        f[mn] through f[(m+1)n-1]: base_f[n-1]*qual_f[m-1] through base_f[n-1]*qual_f[m-1] 
                
        """
        self.feature_names.extend(self.base_f.feature_names)
        
        raise NotImplementedError
    
    def extract(self, world, state, loc, action):
        """Extracts the combination of features according to the ordering defined by compute_feature_names()."""
        raise NotImplementedError


                       