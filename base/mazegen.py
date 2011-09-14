#! /usr/bin/env python

import random
import sys

# Width and height of maze needs to be an even number because of walls
WIDTH = 20
HEIGHT = 20
WALL = "%"
FLOOR = '.'

# The change in x and y for all four directions
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

def recursive_maze(maze, x=0, y=0, dirx=0, diry=0):
    # Check if current position is inside maze boundry
    if 0 <= y < len(maze):
        if 0 <= x < len(maze[0]):
            # Check if this position can have a new hallway going to it
            if maze[y][x] == WALL:
                # Make this position into a hallway
                maze[y][x] = FLOOR

                # Connect this position with previous position
                maze[y-diry][x-dirx] = FLOOR

                # Create direction list and randomize it's order
                directions = [UP, DOWN, LEFT, RIGHT]
                random.shuffle(directions)

                # Follows each direction when the callstack returns here
                for dx, dy in directions:
                    # Go down this current direction
                    recursive_maze(maze, x + dx*2, y + dy*2, dx, dy)

def draw_maze(maze):
    # Draw top wall
    print "rows ",HEIGHT
    print "cols ",WIDTH
    print "players 1"
    # Draw each line with left wall added in
    print "m " + "%"*WIDTH
    print "m a" + "".join(maze[0][1:])
    for line in maze[1:-3]:
        print "m " + "".join(line)
    print "m " + "".join(maze[-2][0:-2]) + "*%"
    print "m " + "%"*WIDTH

if __name__ == '__main__':

    HEIGHT = int(sys.argv[1])
    WIDTH = int(sys.argv[2])
    
    # Initialize the maze as am array of arrays filled with wall spaces
    maze = [[WALL for j in xrange(WIDTH)] for i in xrange(HEIGHT)]
    # Start making the maze
    recursive_maze(maze)
    # Finally, draw it
    draw_maze(maze)