'''
Created on Oct 1, 2011

@author: djweiss
'''
import math

class GridLookup:
    def __init__(self, points, height, width, resolution):
        self.height = height
        self.width = width
        self.resolution = resolution
        
        # Compute grid dimensions
        self.grid_width = math.floor(self.width/resolution)
        self.grid_height = math.floor(self.height/resolution)
        
        self.grid = {}
        
        for row,col in points:

            # Compute grid coordinates            
            g_row = int(row/resolution)
            g_col = int(col/resolution)
            
            for d_row in [-1, 0, 1]:
                for d_col in [-1, 0, 1]:
                    
                    r = g_row+d_row
                    c = g_col+d_col
                    if r < 0: 
                        r = r + self.grid_height
                    else:
                        r = r % self.grid_height
                    if c < 0:
                        c = c + self.grid_width
                    else:
                        c = c % self.grid_width
                    
                    key = (r, c)
                    if self.grid.has_key(key):
                        self.grid[key] += [(row,col)]
                    else:
                        self.grid[key] = [(row,col)]  

    def nearby_points(self, point):
        g_row = int(point[0]/self.resolution)
        g_col = int(point[1]/self.resolution)
        if self.grid.has_key( (g_row,g_col) ):
            return self.grid[(g_row, g_col)]
        else:
            return list()
 
class GlobalState:
    cutoff = 25
        
    def __init__(self, world, resolution): 
        self.world = world
    
        # Parse all possible points of interest
        if len(world.enemies) > GlobalState.cutoff:
            self.grid_enemy = GridLookup(world.enemies, world.height, world.width, resolution)
        else:
            self.grid_enemy = None
                 
        if len(world.food) > GlobalState.cutoff:             
            self.grid_food = GridLookup(world.food, world.height, world.width, resolution)
        else:
            self.grid_food = None
        
        if len(world.ants) > GlobalState.cutoff:
            ant_locs = [ant.location for ant in self.world.ants] 
            self.grid_friendly = GridLookup(ant_locs, world.height, world.width, resolution)
        else:
            self.grid_friendly = None  
        
    def lookup_nearby_food(self, loc):
        if self.grid_food is None:
            return self.world.food

        return self.grid_food.nearby_points(loc)

    def lookup_nearby_friendly(self, loc):
        
        ant_locs = [ant.location for ant in self.world.ants if ant.location != loc]
        if self.grid_friendly is None:
            return ant_locs

        # remove the query point from the lookup        
        return self.grid_friendly.nearby_points(loc)

    def lookup_nearby_enemy(self, loc):
        if self.grid_enemy is None:
            return self.world.enemies
        
        return self.grid_enemy.nearby_points(loc)

