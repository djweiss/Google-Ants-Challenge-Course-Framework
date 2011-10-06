#!/usr/bin/env python
# Created: September 2011
# Author: David Weiss
#
# This batch version of LocalEngine will run a game silently and simply return bot scores.
# It can also provide a bit more feedback optionally.

import sys
from optparse import OptionParser
from worldstate import AntWorld
from antsbot import *
from antsgame import *
from logutil import *
from copy import deepcopy
from mapgen import SymmetricMap
import time

# Whether or not to crash the entire game upon invalid moves
STRICT_MODE = True

# A slightly modified version of the original Ants game from
# antsgame.py: this breaks up the finish_turn() method of the original
# Ants into two separate functions: FinishTurnMoves() and
# FinishTurnResolve(), which are explained above.
class StepAnts(Ants):
    def __init__(self, options=None):
        Ants.__init__(self, options)
      
    def Reset(self, map_text): 
        map_data = self.parse_map(map_text)

        self.turn = 0
        self.num_players = map_data['num_players']

        self.current_ants = {} # ants that are currently alive
        self.killed_ants = []  # ants which were killed this turn
        self.all_ants = []     # all ants that have been created

        self.all_food = []     # all food created
        self.current_food = {} # food currently in game

        # initalise scores
        self.score = [Fraction(0,1)]*self.num_players
        self.score_history = [[s] for s in self.score]
        self.bonus = [0 for s in self.score]

        # initialise size
        self.height, self.width = map_data['size']
        self.land_area = self.height*self.width - len(map_data['water'])

        # initialise map
        self.map = [[LAND]*self.width for i in range(self.height)]

        # initialise water
        for row, col in map_data['water']:
            self.map[row][col] = WATER

        # initalise ants
        for owner, locs in map_data['ants'].items():
            for loc in locs:
                self.add_ant(loc, owner)

        # initalise food
        for loc in map_data['food']:
            self.add_food(loc)

        # track which food has been seen by each player
        self.seen_food = [set() for i in range(self.num_players)]

        # used to remember where the ants started
        self.initial_ant_list = sorted(self.current_ants.values(), key=operator.attrgetter('owner'))
        self.initial_access_map = self.access_map()

        # cache used by neighbourhood_offsets() to determine nearby squares
        self.offsets_cache = {}

        # used to track dead players, ants may still exist, but order are not processed
        self.killed = [False for i in range(self.num_players)]

        # used to give a different ordering of players to each player
        #   initialised to ensure that each player thinks they are player 0
        self.switch = [[None]*self.num_players + range(-5,0) for i in range(self.num_players)]
        for i in range(self.num_players):
            self.switch[i][i] = 0
        # used to track water and land already reveal to player
        # ants and food will reset spots so a second land entry will be sent
        self.revealed = [[[False for col in range(self.width)]
                          for row in range(self.height)]
                         for p in range(self.num_players)]
        # used to track what a player can see
        self.init_vision()

        # the engine may kill players before the game starts and this is needed to prevent errors
        self.orders = [[] for i in range(self.num_players)]

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
    def warning(self, text):
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
        self.bot_time = {}        
        
        L = logging.getLogger("default") 
        L.setLevel(level)
        self.turn_phase = 0
        self.map_list = []
        self.game = None
        
    def RunTournament(self, num_games, team_a_bots, team_b_bots, map_dims):
        """ Play a multi-game tournament between two teams of bots.
        
        For each bot in the lists team_a_bots and team_b_bots, plays num_games on random maps with
        sizes randomly generated between map_dims[0] and map_dims[1].
        
        Returns a 4-tuple:
        (bot_scores,       - The score of each bot on each its games
         bot_wins,         - Whether or not each bot won for each of its games
         bot_score_diffs,  - The score differential for each bot's games (> 0 = won)
         bot_games         - The number of games played by each bot.
         )
        
        """
        
        assert(self.game is not None)
        self.bot_time = {}
                        
        played_games = 0
        start_time = time.time()
        bot_wins = [[0 for i in range(0, len(team_a_bots))], 
                    [0 for i in range(0, len(team_b_bots))]]                    
        bot_scores = deepcopy(bot_wins)
        bot_score_diffs = deepcopy(bot_wins)
        bot_games = deepcopy(bot_wins)
        
        total_turns = 0
        for i in range(0, num_games):
            random_map = SymmetricMap(min_dim=map_dims[0], max_dim=map_dims[1])
            random_map.random_walk_map()

            # Play all possible matchups between team A and team B
            
            status_string = "[map %d] " % i
            if i > 0:
                elapsed = time.time() - start_time
                avg_time = elapsed/i
                remaining = (num_games-i)*avg_time
                
                remaining_str = time.strftime("%H:%M:%S", time.gmtime(remaining))
                status_string += "%s remaining " % remaining_str
            else:
                status_string += "??:??:?? remaining "
            sys.stdout.write(status_string)
            sys.stdout.flush()
            
            for a in range(0, len(team_a_bots)):
                for b in range(0, len(team_b_bots)): 
            
                    # Run the bots against each other 
                    self.game.Reset(random_map.map_text())
                    self.bots = [(0, team_a_bots[a]), (1, team_b_bots[b])]
                    for botnum, bot in self.bots:
                        bot.world = self.GetWorld()
                        bot.reset()
                        bot.world.L = FakeLogger()
                    self.Run()
                    
                    # Record the scores
                    if self.game.score[0] > self.game.score[1]:
                        bot_wins[0][a] += 1
                    else:
                        bot_wins[1][b] +=1
                    bot_scores[0][a] += self.game.score[0]
                    bot_scores[1][b] += self.game.score[1]
        
                    bot_score_diffs[0][a] += self.game.score[0]-self.game.score[1]
                    bot_score_diffs[1][b] += self.game.score[1]-self.game.score[0]
                    
                    bot_games[0][a] += 1
                    bot_games[1][b] += 1
                    played_games += 1
                    total_turns += self.game.turn
                    sys.stdout.write(".")
                    sys.stdout.flush()
            
            a_win_rate = max([float(bot_wins[0][j]) / float(bot_games[0][j]) for j in range(0, len(team_a_bots))]) 
            b_win_rate = max([float(bot_wins[1][j]) / float(bot_games[1][j]) for j in range(0, len(team_b_bots))])
            sys.stdout.write(" max A rate: %.2f, max B rate: %.2f\n" % (a_win_rate, b_win_rate))
            #print elapsed, " - map", i, ": team A bot_scores", str([float(s) for s in bot_scores[0]])
            #print elapsed, " - map", i, ": team B bot_scores", str([float(s) for s in bot_scores[1]])                                                        
        
        elapsed = time.time() - start_time        
        sum_bots = 0
        print "Time summary: %.2f s total = %.2f s/game (%.2f turns/game) " % (elapsed, elapsed/played_games, total_turns/played_games)
        for b in self.bot_time.keys():
            sum_bots += self.bot_time[b]
            print "\tbot %s: %.5f s = %.2f%%" % (b, self.bot_time[b], self.bot_time[b]/elapsed*100)     
        print "\tengine: %.5f s = %.2f%%" % (elapsed-sum_bots, (elapsed-sum_bots)/elapsed*100)
        
        return (bot_scores, bot_wins, bot_score_diffs, bot_games)
        
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
        self.bot_time[str(bot.__class__)] = 0
        
    def PrepareGame(self, argv):
        """ Create a instance of StepAnts and set game options from arguments.""" 
        
        # Parse command line options and fail if unsuccessful.
        self.game_opts = self.GetOptions(argv)
        if self.game_opts == None:
            return -1

        L.debug("Starting local game...")
        L.debug("Using bots: ")
        for b,bot in self.bots:
            L.debug("\tbot %d: %s" % (b, str(bot.__class__)))

        self.game = StepAnts(self.game_opts)
        L.debug("Game created.");

    # Runs the game until completion. Parses command line options.
    def Run(self):
        
        self.turn_phase = 0
        self.turn = 0
        while True:  
            if self.RunTurn() == 0:
                break
        
        for b in self.bots:
            L.info("bot %d: %.02f points" % (b[0], float(self.game.score[b[0]])))
      
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
                start_time = time.time()
                moves = bot._receive(msg)
                elapsed = time.time() - start_time
                if str(bot.__class__) in self.bot_time.keys():
                    self.bot_time[str(bot.__class__)] += elapsed
                else:
                    self.bot_time[str(bot.__class__)] = elapsed
                      
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
                errstr = "bot %d gave ignored orders:\n%s" % (b,'\n'.join(ignored))
                L.warning(errstr)
                if STRICT_MODE == True:
                    raise Exception("One or more bots gave bad orders: " + errstr)
            if len(invalid) > 0:
                errstr = "bot %d gave invalid orders:\n%s" % (b,'\n'.join(invalid))
                L.warning(errstr)
                if STRICT_MODE == True:
                    raise Exception("One or more bots gave bad orders: " + errstr)

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


    
