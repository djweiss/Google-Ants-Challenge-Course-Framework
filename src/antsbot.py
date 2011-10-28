#!/usr/bin/env python
# Created: July 2011
# Author: David Weiss
#
# A base class for Ant bots that are compatible with the
# LocalEngine. They also automatically keep the AntWorld state updated
# based on messages from the server/engine.

import sys
import traceback

from worldstate import Ant, AntStatus, AntWorld

class AntsBot(object):
    def __init__(self, world):
        self.world = world

    def do_turn(self):
        '''Template for logic that must be filled in by the child bot.'''
        raise NotImplemented
    
    def reset(self):
        pass    

    def _receive(self, msg, engine_ants=None):
        '''Parses message from the server/engine and returns output.'''
        lines = msg.splitlines()
        if lines[-1].lower() == 'ready':
            self.world._setup_parameters('\n'.join(lines[:-1]))
            return self.world._finish_turn()

        elif lines[-1].lower() == 'go':
            self.world._update('\n'.join(lines[:-1]),engine_ants)
            self.do_turn()
            return self.world._finish_turn()
        
        return ""

    def _run(self):
        '''Run the bot as a stand-alone process for communicating via stdin/stdout with an Ants engine. NOT the LocalEngine.'''
        map_data = ''

        while True:
            try:
                current_line = raw_input()
                if current_line.lower() == 'ready':
                    
                    self.world._setup_parameters(map_data)
                    self.world._finish_turn()
                    map_data = ''
                    
                elif current_line.lower() == 'go':
                    
                    self.world._update(map_data)
                    self.do_turn()
                    self.world._finish_turn()
                    map_data = ''
                else:
                    map_data += current_line + '\n'
            except EOFError:
                break
            except Exception as e:
                traceback.print_exc(file=sys.stderr)
                break
                    