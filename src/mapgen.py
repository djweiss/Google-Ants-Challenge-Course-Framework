#!/usr/bin/env python

import math
import random

#functions	
def gcd(a, b):
    while b:
        a, b = b, a%b
    return a
        
def lcm(a, b):
    if a == 0 and b == 0:
        return 0
    else:
        return abs(a*b)/gcd(a,b)

#map class
class SymmetricMap():
    cdirections = ['N', 'E', 'S', 'W']
    directions = {'N': (-1,0), 'S': (1,0), 'E': (0,1), 'W': (0,-1)}
    
    no_extra_walks = 30

    #map parameters
    no_players = 0
    rows = cols = 0
    row_t = col_t = 0
    water_squares = 0
    land_squares = 0
    map_data = []
    times_visited = []
    a_loc = c_locs = []
    
    def __init__(self, min_players=2, max_players=2, min_dim=20, max_dim=20, 
                 min_start_distance=5, min_land_proportion=0.75, max_land_proportion=0.9):
        #game parameters
        self.min_players = min_players
        self.max_players = max_players
        self.min_dim = min_dim
        self.max_dim = max_dim
        self.min_start_distance = min_start_distance
        self.min_land_proportion = min_land_proportion
        self.max_land_proportion = max_land_proportion

    #makes a map by performing a bunch of random walks carving out water
    def random_walk_map(self):
        self.pick_dimensions()
        self.map_data = [ ['%' for c in range(self.cols)] for r in range(self.rows) ]
        self.add_ants()
        self.start_walks()
        self.add_walk_land()
    
    #outputs the map
    def print_map(self):
        print "rows", self.rows
        print "cols", self.cols
        print "players", self.no_players
        for row in self.map_data:
            print 'm', ''.join(row)
    
    def map_text(self):
        txt = 'rows ' + str(self.rows) + '\n'
        txt += 'cols ' + str(self.cols) + '\n'
        txt += 'players ' + str(self.no_players) + '\n'
        for row in self.map_data:
            txt += 'm ' + ''.join(row) + '\n'
        
        return txt
        
    #picks the dimensions of the map
    def pick_dimensions(self):
        while True:
            while True:
                self.rows = random.randint(self.min_dim, self.max_dim)
                self.cols = random.randint(self.min_dim, self.max_dim)
            
                self.row_t = random.randint(3, self.rows-3)
                self.col_t = random.randint(3, self.cols-3)
                
                #makes sure no two players start in the same row or column
                if self.rows/gcd(self.row_t, self.rows) == self.cols/gcd(self.col_t, self.cols):
                    break

            self.no_players = lcm(self.rows/gcd(self.row_t, self.rows), 
                                  self.cols/gcd(self.col_t, self.cols) )
            
            #forces a valid number of players all starting at a valid distance
            if self.no_players >= self.min_players and self.no_players <= self.max_players and self.is_valid_start():
                break
    
    #returns the distance between two squares
    def distance(self, loc1, loc2):
        d1 = abs(loc1[0] - loc2[0])
        d2 = abs(loc1[1] - loc2[1])
        dr = min(d1, self.rows - d1)
        dc = min(d2, self.cols - d2)
        return math.sqrt(dr*dr + dc*dc)
    
    #randomly picks a location inside the map
    def pick_square(self):
        return [random.randint(0, self.rows-1), random.randint(0, self.cols-1)]

    #starts two random walks from the players starting ants
    def start_walks(self):
        self.c_locs = [self.a_loc, self.a_loc]
        for w in range(self.no_extra_walks):
            self.c_locs.append(self.pick_square())

    #walks the random walk locations
    def walk_locations(self):
        for c in range(len(self.c_locs)):
            d = self.cdirections[random.randint(0, 3)]
            self.c_locs[c] = self.get_loc(self.c_locs[c], d)
    
    #returns the new location after moving in a particular direction
    def get_loc(self, loc, direction):                                    
        dr, dc = self.directions[direction]                              
        return [(loc[0]+dr)%self.rows, (loc[1]+dc)%self.cols ]
        
    #returns the new location after translating it by (rtranslate, ctranslate)
    def get_translate_loc(self, loc):
        return [(loc[0]+self.row_t)%self.rows, 
                (loc[1]+self.col_t)%self.cols ]
    
    #fills in all symmetrically equivalent squares with the given type
    def fill_squares(self, loc, type):
        value = type
        for n in range(self.no_players):
            self.map_data[loc[0] ][loc[1] ] = value
            if type == 'a':
                value = chr(ord(value)+1)
            loc = self.get_translate_loc(loc)
    
    #checks whether the players start far enough apart
    def is_valid_start(self):
        loc = n_loc = [0,0]
        for n in range(self.no_players-1):
            n_loc = self.get_translate_loc(n_loc)
            if self.distance(loc, n_loc) < self.min_start_distance:
                return False
        return True
    
    #checks whether the players can reach every non-wall square
    def is_valid(self):
        start_loc = self.a_loc
        visited = [ [False for c in range(self.cols)] for r in range(self.rows)]
        visited[start_loc[0] ][start_loc[1] ] = True
        squaresVisited = 1
        
        stack = [start_loc]
        while stack:
            c_loc = stack.pop()
            for d in self.directions:
                n_loc = self.get_loc(c_loc, d)
                    
                if not visited[n_loc[0]][n_loc[1]] and self.map_data[n_loc[0]][n_loc[1]] != '%':
                    stack.append(n_loc)
                    visited[n_loc[0] ][n_loc[1] ] = True
                    squaresVisited += 1

        if squaresVisited == self.land_squares:
            return True
        return False
    
    #adds ants to the map
    def add_ants(self):
        self.land_squares = self.no_players
        self.a_loc = self.pick_square()
        self.fill_squares(self.a_loc, 'a')
    
    #adds land to a map of water
    def add_walk_land(self):
        #random.gauss(2,10)
        no_land_squares = random.randint(int(self.min_land_proportion*self.rows*self.cols), 
                                          int(self.max_land_proportion*self.rows*self.cols))
        
        while self.land_squares < no_land_squares or not self.is_valid():
            self.walk_locations()

            for c_loc in self.c_locs:
                if self.map_data[c_loc[0]][c_loc[1]] == '%':
                    self.land_squares += self.no_players
                    self.fill_squares(c_loc, '.')

if __name__ == '__main__':
    import optparse
    
    parse = optparse.OptionParser()
    parse.add_option("-n", "--num_players", default=2, type="int",
                     dest="num_players", help="Number of players on map.")
    parse.add_option("-l", "--min_dimension", default=30, type="int",
                     dest="min_dim", help="Map min dimensions.")
    parse.add_option("-u", "--max_dimensions", default=30, type="int",
                     dest="max_dim", help="Map max dimensions.")

    (options, args) = parse.parse_args()
    
    example_map = SymmetricMap(min_players=options.num_players, max_players=options.num_players,
                               min_dim=options.min_dim, max_dim=options.max_dim)
    example_map.random_walk_map()
    example_map.print_map()

#def __init__(self, min_players=2, max_players=2, min_dim=20, max_dim=20, 
#                 min_start_distance=5, min_land_proportion=0.75, max_land_proportion=0.9):
    
