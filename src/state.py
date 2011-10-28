'''
Created on Oct 1, 2011

@author: djweiss
'''
import math
import worldstate

class GridLookup:     
    """ Datastructure that, once created, allows the lookup of nearby points to query point in constant time.
    
    The GridLookup works as follows: it divides the map into a grid of size <lookup_res> cells.
    
    For all input points, it computes the grid location of the 9 grid cells that either contain 
    the given point or are adjacent, allowing for wrap-around in the infinite wrap-around map.
    
    Thus, each grid cell is a bucket in a dictionary containing points that are within one grid cell 
    adjacent to the lookup cell. Thus, we can build this data structure in constant time,
    and lookup nearby points within 2*<lookup_res> manhattan distance of the query point.

    """
    
    def __init__(self, points, height, width, resolution):
        """Initializes lookup table with a set of points, diving a 
        width X height grid into size lookup_res cells.
        
        """
        self.height = height
        self.width = width
        self.lookup_res = resolution
        
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
        """Lookup points within 2*lookup_res manhattan distance of query point."""
        
        g_row = int(point[0]/self.lookup_res)
        g_col = int(point[1]/self.lookup_res)
        if self.grid.has_key( (g_row,g_col) ):
            return self.grid[(g_row, g_col)]
        else:
            return list()
 
class GlobalState:
    """Template class storing useful datastructure that is helpful for maintaining state between multiple ants.
    
    Feel free to modify this class as you see fit for HW3. Keep in mind that ValueBot instantiates GlobalState from
    the world, so you may need to change the ValueBot.do_turn() method if you change this state significantly.
    
    By default, this GlobalState class does not create lookup tables unless there are at least 25 points of interest (enemies,
    food, or friendly ants.) 
    
    This GlobalState class also implements, as an example of another useful thing to keep track of, how many times positions
    on the map have been visited, at a coarse resolution than individual squares. It demonstrates how to use the new RenderHeatMap()
    method of LocalEngine which is useful to give a visual representation of map data for debugging purposes in the update() method.
    """    
    
    cutoff = 25   # When to use the lookup table, and when not.
        
    def __init__(self, world, resolution, visited_cells=10, draw_heatmap=True): 
        self.world = world
        self.lookup_res = resolution
        self.visited_res = int(min(self.world.height/visited_cells, self.world.width/visited_cells))
        self.visited = {}

        self.draw_heatmap = False
                
        self.update()
        
    def update(self):
        world = self.world
        
        # Parse all possible points of interest
        if len(world.enemies) > GlobalState.cutoff:
            self.grid_enemy = GridLookup(world.enemies, world.height, world.width, self.lookup_res)
        else:
            self.grid_enemy = None
                 
        if len(world.food) > GlobalState.cutoff:             
            self.grid_food = GridLookup(world.food, world.height, world.width, self.lookup_res)
        else:
            self.grid_food = None
        
        if len(world.ants) > GlobalState.cutoff:
            ant_locs = [ant.location for ant in self.world.ants] 
            self.grid_friendly = GridLookup(ant_locs, world.height, world.width, self.lookup_res)
        else:
            self.grid_friendly = None
            
        # Update visited states
        for ant in self.world.ants:
            key = self._visited_key(ant.location)
            if self.visited.has_key(key):
                self.visited[key] += 1
            else:
                self.visited[key] = 1
                
        # This is very important: do not import localengine at top of python file or else your code will
        # not be able to run on the competition server. 
        if self.world.engine is not None:
            from src.localengine import LocalEngine
            if self.world.engine.__class__ == LocalEngine and self.draw_heatmap:
                heatmap = [ [self.get_visited((row,col)) for col in range(0, self.world.width)] for row in range(0,self.world.height)]
                self.world.engine.RenderHeatMap(heatmap, window="Visited", minval=0, maxval=5)
        
    def lookup_nearby_food(self, loc):
        """Returns food within 2*lookup_res manhattan distance if n > 25, otherwise all food."""
        
        if self.grid_food is None:
            return self.world.food

        return self.grid_food.nearby_points(loc)

    def lookup_nearby_friendly(self, loc):
        """Returns friendlies within 2*lookup_res manhattan distance if n > 25, otherwise all friends."""
        
        ant_locs = [ant.location for ant in self.world.ants if ant.location != loc]
        if self.grid_friendly is None:
            return ant_locs

        # remove the query point from the lookup        
        return self.grid_friendly.nearby_points(loc)

    def lookup_nearby_enemy(self, loc):
        """Returns enemies within 2*lookup_res manhattan distance if n > 25, otherwise all enemies."""
        
        if self.grid_enemy is None:
            return self.world.enemies
        
        return self.grid_enemy.nearby_points(loc)

    def _visited_key(self, loc):
        """Get the coarse resolution location for keeping track of visited positions."""
        
        row,col = loc
        row = row % self.world.height
        col = col % self.world.width
        cell_row = row / self.visited_res
        cell_col = col / self.visited_res
        return (cell_row, cell_col)
    
    def get_next_visited(self, loc, action):
        """Returns the number of times the next location in this direction has been visited."""
         
        direction = worldstate.AIM[action]
        next_loc = [loc[i]+self.visited_res*direction[i] for i in range(0, len(direction))]
        return self.get_visited(next_loc)

    def get_visited(self, loc):
        """Returns the number of times this location has been visited.""" 
        
        key = self._visited_key(loc)
        if self.visited.has_key(key):
            return self.visited[key]
        else:
            return 0
    
