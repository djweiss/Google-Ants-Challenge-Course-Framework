#!/usr/bin/env python
# Created: July 2011
# Author: David Weiss
#
# A base class for Ant bots that are compatible with the
# LocalEngine. They also automatically keep the AntWorld state updated
# based on messages from the server/engine.

from worldstate import Ant, AntStatus, AntWorld
import traceback, sys

class AntsBot:
    def __init__(self, world):
        self.world = world

    # Template for logic that must be filled in by the child bot.
    def DoTurn(self):
    # Default logic: WAGONS WEST!!
        for ant in self.world.ant_list:
            if ant.status == AntStatus.ALIVE:
                ant.direction = 'w'

    # Parses message from the server/engine and returns output.
    def Receive(self, msg):
        lines = msg.splitlines()
        if lines[-1].lower() == 'ready':
            self.world.SetupParameters('\n'.join(lines[:-1]))
            return self.world.FinishTurn()

        elif lines[-1].lower() == 'go':
            self.world.Update('\n'.join(lines[:-1]))
            self.DoTurn()
            return self.world.FinishTurn()
    
        return ""

    # Run the bot as a stand-alone process for communicating via
    # stdin/stdout with an Ants engine. NOT the LocalEngine.
    def Run(self):
        map_data = ''

        while(True):
            try:
                current_line = raw_input()
                if current_line.lower() == 'ready':

                    self.world.SetupParameters(map_data)
                    self.world.FinishTurn()
                    map_data = ''

                elif current_line.lower() == 'go':
                    self.world.Update(map_data)
                    self.DoTurn()
                    self.world.FinishTurn()
                    map_data = ''
                else:
                    map_data += current_line + '\n'
            except EOFError:
                break
            except Exception as e:
                traceback.print_exc(file=sys.stderr)
                break
