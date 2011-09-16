#!/usr/bin/env python
# Created: September 2011
# Author: David Weiss
#
# This batch version of LocalEngine will run a game silently and simply return bot scores.
# It can also provide a bit more feedback optionally.

import sys
import traceback
import operator
import string
import os

from optparse import OptionParser
from math import sqrt,floor
from collections import deque, defaultdict
from fractions import Fraction

from logutil import *
from game import Game
from worldstate import AntStatus,Ant,AntWorld
from antsbot import *
from antsgame import * # Importing * is required to get all of the
                                              # constants from antsgame.py

# Whether or not to crash the entire game upon invalid moves
STRICT_MODE = False

#global gui
#gui = Frame()    # This is the Tk master object from which all GUI
                              # elements will spawn

# A lookup table for visualizing the map
MapColors = [
            'red', # ant color 1
            'blue', # ant color 2
            'green', # ant color 3
            'orange', # ant color 4
            'magenta', # ant color 5
            'cyan', # ant color 6
            '#000', # unseen
            '#fee', # conflict(?)
            '#88f', # water
            '#fff', # food
            '#666', # land
]

# A slightly modified version of the original Ants game from
# antsgame.py: this breaks up the finish_turn() method of the original
# Ants into two separate functions: FinishTurnMoves() and
# FinishTurnResolve(), which are explained above.
class StepAnts(Ants):
    def __init__(self, options=None):
        Ants.__init__(self, options)
      
    def FinishTurnMoves(self): # Content copied from Ants.finish_turn()
        # Determine players alive at the start of the turn.  Only these
        # players will be able to score this turn.
        self.was_alive = set(i for i in range(self.num_players) if self.is_alive(i))
        self.do_orders()

    def FinishTurnResolve(self): # Content copied from Ants.finish_turn()
        # Run attack, food, etc. resolution and scoring.
        self.do_attack()
        self.do_spawn()
        self.food_extra += Fraction(self.food_rate * self.num_players, self.food_turn)
        food_now = self.food_extra // self.num_players
        self.food_extra %= self.num_players
        self.do_food(food_now)

        # Computes scores for each player.
        for i, s in enumerate(self.score):
            if i in self.was_alive:
                # Update score for those were alive at the START of the turn.
                self.score_history[i].append(s)
            else:
                # Otherwise undo any changes to their score made during this
                # turn.
                self.score[i] = self.score_history[i][-1]
                
        # Since all the ants have moved we can update the vision.
        self.update_vision()
        self.update_revealed()

class FakeLogger:
    def debug(self, text):
        None
        # do nothing
    def info(self, text):
        None
        # do nothing
    def error(self, text):
        None
        # do nothing
        
# The actual local engine class. See top of file for description.
class BatchLocalEngine:

    def __init__(self, game=None, level=logging.CRITICAL):
        self.bots = []

        L = logging.getLogger("default") # Use the same logger as the
                                         # default, so the log also goes
                                         # to the console.
        L.setLevel(level)
        self.turn_phase = 0

    # Returns a new AntWorld with engine set properly for use by client bots.
    def GetWorld(self):
        return AntWorld(engine=self)

    # Adds a given AntsBot object to the list of bots playing the game,
    # and creates a log window for the bot.
    def AddBot(self, bot):
        b = len(self.bots)

        # Setup log window for specific bot.
        bot.world.L = FakeLogger()
        # Add to internal list for playing the game.
        self.bots.append((b, bot))

    def PrepareGame(self, argv):
        # Parse command line options and fail if unsuccessful.
        self.game_opts = self.GetOptions(argv)
        if self.game_opts == None:
            return -1

        L.debug("Starting local game...")
        L.debug("Using bots: ")
        for b,bot in self.bots:
            L.debug("\tbot %d (%s): %s" % (b, MapColors[b],str(bot.__class__)))

        self.game = StepAnts(self.game_opts)

        L.debug("Game created.");
        
    # Runs the game until completion. Parses command line options.
    def Run(self):

        self.turn = 0
        while True:  
            if self.RunTurn() == 0:
                break
        
        for b in self.bots:
            L.info("bot %d (%s): %.02f points" % (b[0],MapColors[b[0]],float(self.game.score[b[0]])))
#        gui.mainloop()
      
    # Tk callback event for stepping through to the next turn.
    def RunTurnCallback(self, event):
        try:
            self.RunTurn()
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
            sys.exit()

    # Steps through 1/2 of a turn.
    def RunTurn(self):
        game = self.game  # shortcut

        if self.turn == game.turns or game.game_over():
            L.info("Game finished at turn %d" % self.turn);
            L.info("Game over? " + str(game.game_over()))
            #gui.quit()
            game.finish_game()
            return 0
    
        # Initial turn is a special case. 
        if self.turn == 0:
            L.debug("Starting game....")
            game.start_game()

            # For debugging, keep track of what water was revealed to which
            # bot (this was a very annoying bug).
            self.water = [game.revealed_water[b] for b in range(game.num_players)]

            # Send starting game state to bots, but don't do anything with
            # their response.
            self.SendAndRcvMessages() 

            # Turn 0 is over. Now 1/2 phase turns can begin.
            self.turn += 1

        if self.turn_phase == 0: # Movement phase, beginning of turn
            L.debug("Starting turn: %d" % self.turn)

            # Send game state from last turn to bots and get messages.
            self.SendAndRcvMessages()        
            game.FinishTurnMoves()

            self.turn_phase = 1

        else: # Combat, food, etc. resolution phase
            
            # Finish game turn logic.
            game.FinishTurnResolve()

            # Again, keep track of revealed water for bugfinding.
            for p in range(len(self.bots)):
                self.water[p] = self.water[p] + game.revealed_water[p]
            
            # Reset turn phase and advance turn.
            self.turn_phase = 0 
            self.turn += 1

            # Sanity check: make sure that water that is visible actually
            # was revealed to the player.
            for p in range(len(self.bots)):
                for row, squares in enumerate(game.vision[p]):
                    for col, visible in enumerate(squares): 
                        if game.map[row][col] == WATER and visible:
                            if (row,col) not in self.water[p]:
                                L.error("water square %d,%d is visible to player %d but not revealed" % (row,col,p))

        # Update the map regardless of turn phase. 
        #self.RenderMap(game.get_perspective(0));
        
      

    # Sends game states to bots, receives messages, and clears game
    # state for the next turn.
    def SendAndRcvMessages(self):
        game = self.game

        bot_moves = []  # Movement cache

        for b, bot in self.bots:
            msg = None

            # Get message to send to player depending on turn.
            if self.turn == 0:
                msg = game.get_player_start(b) + 'ready\n'
            else:
                msg = game.get_player_state(b) + 'go\n'

            # Send message and receive reply.
            if game.is_alive(b):
                L.debug("Bot %d is alive" % b)
                L.debug("Sending message to bot %d:\n%s" % (b, msg))
                moves = bot._receive(msg)
                L.debug("Received moves from bot %d:\n%s" % (b, '\n'.join(moves)))
                bot_moves.append((b, moves))

        # Clear the old turn's game state now that it's been sent to the
        # player. NOTE: The game parameters get sent on turn 0, but the
        # initial world state does not get sent until turn 1. Therefore do
        # not reset game state until after turn 0.
        if self.turn > 0:
            game.start_turn()

        # Have the game process the cached moves.
        for b,moves in bot_moves:
            valid, ignored, invalid = game.do_moves(b, moves)
            if len(ignored) > 0:
                L.warning("bot %d gave ignored orders:\n%s" % 
                                (b,'\n'.join(ignored)))
                if STRICT_MODE == True:
                    raise Exception("One or more bots gave bad orders")
            if len(invalid) > 0:
                L.warning("bot %d gave invalid orders:\n%s" % 
                                (b,'\n'.join(invalid)))
                if STRICT_MODE == True:
                    raise Exception("One or more bots gave bad orders")

        L.debug("Game should execute orders:\n%s" % 
                            str(game.orders))

    # Get game options from command line. Largely copied from the
    # original Ants code.
    def GetOptions(self, argv):
        usage ="Usage: %prog --run [options]"
        parser = OptionParser(usage=usage)

        # I added this as a required option so that the dual-use behavior
        # (see GreedyBot.py) works as expected.
        parser.add_option("--run", dest="runlocal",
                                            action="store_true",
                                            help="Required to run the bot locally")
        # whether to step through every half-turn or just let it run
        parser.add_option("--step-through", dest="step_through",
                                            default=True, type="int",
                                            help="Hit enter to step through turns")
                                            
        # map to be played
        # number of players is determined by the map file
        parser.add_option("-m", "--map_file", dest="map",
                                            default="debug_map.map",
                                            help="Name of the map file")
    
        # maximum number of turns that the game will be played
        parser.add_option("-t", "--turns", dest="turns",
                                            default=1000, type="int",
                                            help="Number of turns in the game")
        parser.add_option("--turntime", dest="turntime",
                                            default=1000, type="int",
                                            help="Amount of time to give each bot, in milliseconds")
        parser.add_option("--loadtime", dest="loadtime",
                                            default=3000, type="int",
                                            help="Amount of time to give for load, in milliseconds")
        parser.add_option("--player_seed", dest="player_seed",
                                            default=0, type="int",
                                            help="Player seed for the random number generator")
        parser.add_option("--engine_seed", dest="engine_seed",
                                            default=None, type="int",
                                            help="Engine seed for the random number generator")
        
        # ants specific game options
        parser.add_option("--attack", dest="attack",
                                            default="power",
                                            help="Attack method to use for engine. (closest, power, support, damage)")
        parser.add_option("--food", dest="food",
                                            default="symmetric",
                                            help="Food spawning method. (none, random, sections, symmetric)")
        parser.add_option("--viewradius2", dest="viewradius2",
                                            default=55, type="int",
                                            help="Vision radius of ants squared")
        parser.add_option("--spawnradius2", dest="spawnradius2",
                                            default=1, type="int",
                                            help="Spawn radius of ants squared")
        parser.add_option("--attackradius2", dest="attackradius2",
                                            default=5, type="int",
                                            help="Attack radius of ants squared")

        (opts, args) = parser.parse_args(argv)
        if opts.runlocal != True:
            parser.print_help()
            return None

        # Check for missing map
        if opts.map is None or not os.path.exists(opts.map):
            sys.stderr.write("Error: Map %s not found\n" % opts.map)
            parser.print_help()
            return None

        # Load map data
        game_options = {
                "map": opts.map,
                "attack": opts.attack,
                "food": opts.food,
                "viewradius2": opts.viewradius2,
                "attackradius2": opts.attackradius2,
                "spawnradius2": opts.spawnradius2,
                "loadtime": opts.loadtime,
                "turntime": opts.turntime,
                "turns": opts.turns,
                "player_seed": opts.player_seed,
                "engine_seed": opts.engine_seed,
                "step_through": opts.step_through }

        with open(opts.map, 'r') as map_file:
            game_options['map'] = map_file.read()

        return game_options


    
