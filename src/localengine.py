#!/usr/bin/env python
# Created: July 2011
# Author: David Weiss
#
# A "local" version of engine.py provided by the Ants game source
# code. The original engine runs bot processes in sandboxed POSIX
# environments, using stdin/out to communicate and suspending
# processes if they run out of time. This version is meant to be
# called as part of a __main__ routine of another class, most likely
# in the test code of a Python bot. 
#
# The local engine logs bot input and output to separate Tk windows
# and provides a live Tk powered map. Turns are advanced by pressing
# any key on the keyboard, press 'Q' to quit. Each keypress advances
# 1/2 turn; the first keypress shows Ant movement, the second shows
# combat and food resolution and updating of the player's vision data.
#
# The local engine makes debugging a bot much easier, as simply
# running the bot python file will try to simulate an entire game, and
# errors that occur will be observed immediately. No poring through
# log files is required.
#
# TODO:
#        - Show graphically which ants will attack each other in combat phase
#        - Display the turn in the title window
#        - Map is currently hard-coded to show player 0's perspective; fix this
#        - Better window geometry layout so they're not all on top of each other.

import sys
import traceback
import operator
import string
import os
import tkFont

from Tkinter import *
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

PLAY_SPEED_MS = 10 #adjust as needed
GAMELOG_BOTNUM = -1 #hacky hack hackerson
# Whether or not to crash the entire game upon invalid moves
STRICT_MODE = False

global gui
gui = Frame()    # This is the Tk master object from which all GUI
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

class LogWindow():#Toplevel):

    # Init takes a botnum parameter to set the title.
    def __init__(self, master=None, botnum=0): 
        #POTENTIALLY TODO HERE: little wrapper frame with a title
        self.textbox = Text(gui,takefocus=0, width=72,height=20, bd=0)
        if botnum != GAMELOG_BOTNUM:
          self.textbox.grid(row=botnum, column=1)
        else:
          self.textbox.grid(row=1, column=0)
        
        # Setup font colors for the difference logging levels through text
        # tags. The emit() function will tag the text appropriately so
        # these styles get applied.
        self.textbox.tag_config("DEBUG", foreground='#999')
        self.textbox.tag_config("INFO", foreground='#000')
        self.textbox.tag_config("WARNING", foreground='#f00')
        self.textbox.tag_config("ERROR", foreground='#f00')
        self.textbox.tag_config("CRITICAL", foreground='#f00', underline=1)
        self.textbox.tag_config("header", underline=1)

        # Set up the scrollbar. (Copied from tutorial).
        #self.scrollY = Scrollbar(self.frame, orient=VERTICAL, command=self.textbox.yview)
        #self.scrollY.grid(row=0, column=1, sticky=N+S)
        #self.textbox["yscrollcommand"] = self.scrollY.set

        # Make a logHandler object and redirect it's emission to me.
        self.log_handler = logging.StreamHandler()
        self.log_handler.emit = self.emit

    def emit(self, log_record):
        # Displays a log record to the textbox and causes the textbox to
        # scroll.

        # Format the message and count the # of lines it will take up.
        head = "[%s:%d]" % (log_record.funcName, log_record.lineno)
        msg = " %s\n" % (log_record.msg)
        lines = len(msg.split('\n'))

        # Insert into the textbox with an extra "header" style underlining
        # just the filename and line number.
        self.textbox.insert(INSERT, head, ("header", log_record.levelname))
        self.textbox.insert(INSERT, msg, (log_record.levelname))
        self.textbox.yview(SCROLL, lines, UNITS)

class Heatmap(Toplevel):
    
    def __init__(self, master=None, engine=None, title="unknown"):
        Toplevel.__init__(self, master=master)
        
        # Make resizable. (Copied from tutorial).
        self.frame = Frame(self)
        self.title(title)
        self.resizable(True,True)

        (self.map, self.mapr, geo, map_geo) = engine.InitMap(self.frame)
        self.geometry(map_geo)


# The actual local engine class. See top of file for description.
class LocalEngine:
    def __init__(self, game=None):
        self.bots = []
        self.heatmaps = {}

        # Set up the main Tk window which will show the map.
        gui.grid()
        gui.master.geometry("100x100+50+50")
        gui.master.title("World View")
        gui.master.resizable(True,True)
        gui.master.lift()

        # Set up callbacks for user input.
#        gui.bind_all("<KeyPress-Return>", self.RunTurnCallback)
#        gui.bind_all("<KeyPress-q>", self.QuitGameCallback)

        # Create a logging window for the main server.
        #HACK! but w/e 
        self.logwindow = LogWindow(gui,botnum=GAMELOG_BOTNUM) 
        #self.logwindow.title("Engine Log")
        L = logging.getLogger("default") # Use the same logger as the
                                         # default, so the log also goes
                                         # to the console.
        L.setLevel(logging.DEBUG)
        L.addHandler(self.logwindow.log_handler)
        self.turn_phase = 0

    # Returns a new AntWorld with engine set properly for use by client bots.
    def GetWorld(self):
        return AntWorld(engine=self)
            

    # Adds a given AntsBot object to the list of bots playing the game,
    # and creates a log window for the bot.
    def AddBot(self, bot):
        b = len(self.bots)

        # Setup log window for specific bot.
        logwindow = LogWindow(botnum=b)
        bot.world.L = logging.getLogger("bot: %d" % b)
        bot.world.L.setLevel(logging.DEBUG)
        bot.world.L.addHandler(logwindow.log_handler)

        # Add to internal list for playing the game.
        self.bots.append((b, bot))

    # Runs the game until completion. Parses command line options.
    def Run(self, run_mode, argv):

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

        self.turn = 0
        
        self.map_frame = Frame(gui)
        gui.map, gui.mapr, geo, map_geo = self.InitMap(self.map_frame)
        gui.master.geometry(geo)
        
        self.InitControls()
        gui.master.lift()
        if run_mode == 'step':
            gui.mainloop()
        elif run_mode == 'play' or run_mode == 'batch': 
            while 1: 
                if run_mode == 'play':
                    gui.update()
                if self.RunTurn(run_mode == 'play') == 0:
                    break
        else:
            raise NotImplementedError
        
        print "*"*20
        print "Game Summary"
        print "*"*20
        for b in self.bots:
            print "bot %d (%s): %.02f points" % (b[0],MapColors[b[0]],float(self.game.score[b[0]]))
        print "-"*20
              


    def InitControls(self):
        """ Gives you play/pause buttons a la normal debugging"""
        self.controls_frame = Frame(self.map_frame)
        step = Button(self.controls_frame, text='Step', \
                      command=self.RunTurnCallback)
        step.grid(row=0, column=0)
#        playpause = Button(self.controls_frame, text='Play/Pause', \
#                           command=self.PlayPauseGameCallback)
#        playpause.grid(row=0, column=1)
        self.controls_frame.grid(row=1, column=0)

    # Draws the rectangles on the Map GUI window that will be used to
    # represent game state.
    def InitMap(self, map_frame):

        mx = self.game.width*20 # Map window dimensions
        my = self.game.height*20
        rx = mx / (self.game.width+2) # Rectangle dimensions
        ry = my / (self.game.height+2)

        # We use a Tk Canvas object for drawing the rectangles.
        mymap = Canvas(map_frame, width=mx,height=my, bg="#AAA")
        mymap.grid(row=0, column=0)
        map_frame.grid(row=0, column=0)

        mapr = list()
        for i in xrange(self.game.height):
            mapr.append([])
            for j in xrange(self.game.width):

                # Get rectangle coordinates and draw the rectangle.
                x0 = rx*(j+1)
                x1 = rx*(j+2)
                y0 = ry*(i+1)
                y1 = ry*(i+2)
                mapr[i].append(
                    mymap.create_rectangle(x0, y0, x1, y1, fill='#fff'))
        
        
        geometry = "%dx%d+0+0" % (mx * 2.6,my * 2)
        map_geo = "%dx%d+0+0" % (mx, my)
        return (mymap, mapr, geometry, map_geo)
        # Update the geometry of the master window to reflect the desired
        # map window size.
        

    # Renders a map based on the mapdata array, where mapdata takes on
    # one of the states from the MapColors array.
    def RenderMap(self, mapdata):
        for i in range(self.game.height):
            for j in range(self.game.width):
                color = '#999'

                # TODO For some reason, sometimes the mapdata gets assigned
                # None and this was causing the code to crash.
                if mapdata[i][j] != None:
                   color = MapColors[mapdata[i][j]]
                else:
                    L.error("mapdata[%d][%d] is None" % (i,j))

                # Update rectangle colors.
                gui.map.itemconfigure(gui.mapr[i][j], fill=color)

    # Renders a colored map to represent arbitrary floating point data
    # values. "Red" is hotter (larger), "Blue" is cooler (smaller).
    def RenderHeatMap(self, mapdata, minval=None, maxval=None, window="heatmap"):
        """ Renders a heatmap of data.
        
        Takes in mapdata in the form of a 2-D list where mapdata[row][col] is some numeric value.
        Plots the mapdata by scaling between blue and red, where blue = minval and red = maxval.
        If minval and maxval are not provided, automatically computes min and max values.
        
        window is the name of the heatmap; for each unique window string, a new heatmap window will be created.
        
        """
        
        if not self.heatmaps.has_key(window):
            self.heatmaps[window] = Heatmap(title=window, engine=self)
        
        heatmap = self.heatmaps[window]

        # Concatenates mapdata into a single list.
        vals = list()
        for i in range(self.game.height):
            for j in range(self.game.width):
                vals.append(float(mapdata[i][j]))

        # Get min and max value if not specified.
        if minval == None:
            minval = min(vals)
        if maxval == None:
            maxval = max(vals)

        # Compute the colormap, blue going into red in 32 distinct
        # hexadecimal colors.
        hexvals = '0123456789abcdef'
        cols = list()
        for i in range(16):
            cols.append('#' + hexvals[i] + hexvals[i] + hexvals[-(i+1)])
        for i in range(16):
            cols.append('#f' + hexvals[-(i+1)] + '0')

        for i in range(self.game.height):
            for j in range(self.game.width):

                # Truncate extreme values.
                c = float(mapdata[i][j])
                if c < minval: 
                    c = minval;
                if c > maxval:
                    c = maxval;

                # Determine which of the 32 colors this square will use.
                colidx = int(floor( ((c-minval)/(maxval-minval) * 31) ))
                if colidx > 32 or colidx < 0:
                    L.error("WTF? colidx = " + str(colidx) + ", c = " + str(c) 
                                    + ", minval = " + str(minval) + ", maxval = " 
                                    + str(maxval))
                heatmap.map.itemconfigure(heatmap.mapr[i][j], fill=cols[colidx])

    # Tk callback event for quitting.
    def QuitGameCallback(self, event):
        L.info("Abort! Quitting...")
        sys.exit()

    # Tk callback event for stepping through to the next turn.
    def RunTurnCallback(self, event=None):
        try:
            self.RunTurn()
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
            sys.exit()

    play_is_on = False #arguably, poor form
    def PlayPauseGameCallback(self, event=None):
        self.play_is_on = not self.play_is_on
        self.PlayUntilStopped()
        
    def PlayUntilStopped(self):
        raise NotImplementedError
    
        if self.play_is_on:
            self.RunTurnCallback()
            gui.after(PLAY_SPEED_MS, self.PlayUntilStopped)

    # Steps through 1/2 of a turn.
    def RunTurn(self, draw_map):
        game = self.game  # shortcut

        if self.turn == game.turns or game.game_over():
            L.info("Game finished at turn %d" % self.turn);
            L.info("Game over? " + str(game.game_over()))
            gui.quit()
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
            
            # clean slate
            for a in self.game.all_ants:
                a.food_amt = 0
                a.kill_amt = 0
            
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
        if draw_map:
            self.RenderMap(game.get_perspective(0));
        
      

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
                
            ants_b = self.game.player_ants(b)

            # Send message and receive reply.
            if game.is_alive(b):
                L.debug("Bot %d is alive" % b)
                L.debug("Sending message to bot %d:\n%s" % (b, msg))
                moves = bot._receive(msg,ants_b)
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
                L.error("bot %d gave ignored orders:\n%s" % 
                                (b,'\n'.join(ignored)))
                if STRICT_MODE == True:
                    raise Exception("One or more bots gave bad orders")
            if len(invalid) > 0:
                L.error("bot %d gave invalid orders:\n%s" % 
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
