'''
Created on Aug 23, 2011

@author: bensapp
'''
from antsgame import AIM

class AntPathSearch():
    ''' This is a base class for all specific search classes. '''
    
    def __init__(self,_world):
        self.world = _world
        
    def get_path(self,start,goal):
        ''' 
        Input: start and goal are both 2-tuples containing (x,y) coordinates
        Output: Returns a list of 2-tuples which are a sequence of locations to get from START to GOAL
            - path[0] should equal START
            - path[-1] should equal GOAL
            - path[i+1] should be reachable from path[i] via exactly one step in some cardinal direction, for all i
        '''
        raise NotImplementedError
        
    def get_successors(self,loc):
        ''' 
        Returns a list of valid next reachable locations from the input LOC.
        All derived classes should use this function, otherwise testing your implementation might fail.        
        '''
        
        alldirs = AIM.keys()
        s = []
        for d in alldirs:
            l = self.world.next_position(loc, d)
            if self.world.passable(l):
                s.append(l)
        return s
         

class BreadthFirstSearch(AntPathSearch):
    
    def get_path(self,start,goal):
        ''' 
        YOUR CODE HERE.
        (See specifications in AntPathSearch.get_path above)
        '''
        return [goal]*100
        
        
class DepthFirstSearch(AntPathSearch):
    
    def get_path(self,start,goal):
        ''' 
        YOUR CODE HERE.
        (See specifications in AntPathSearch.get_path above)
        '''
        return [goal]*100
    
    
class aStarSearch(AntPathSearch):
    
    def heuristic_cost(self,state,goal):
        ''' Make some admissable heuristic for how far we are from the goal ''' 
        return 0
    
    def get_path(self,start,goal):
        ''' 
        YOUR CODE HERE.
        (See specifications in AntPathSearch.get_path above)
        '''
        return [goal]*100