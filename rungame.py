import sys
import os
from optparse import OptionParser

#Main section allowing for dual use either with the standard engine
# or the LocalEngine. If no arguments are given, it calls
# AntsBot.Run() to run as a stand alone process, communicating via
# stdin/stdout. However, if arguments are given, it passes them to
# LocalEngine and creates two instances of GreedyBot to play against
# one another.
if __name__ == '__main__':
    # From Ants distribution: use psyco to speed up all code.
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass

    try:        
        #-3 here is to cut of .py, which is not used in imports
        botlist = [os.path.basename(s) for s in sys.argv[1:] if s[-3:] == '.py']
        arglist = [sys.argv[0]]+[s for s in sys.argv[1:] if s[-3:] != '.py']
        bots = [__import__(botstr[:-3]).BOT for botstr in botlist]
        
        if len(sys.argv) > 2: # Run LocalEngine version
      
            from src.localengine import LocalEngine
            engine = LocalEngine()

            for B in bots:
                engine.AddBot(B(engine.GetWorld()))
            
            engine.Run(arglist)
      
        else: # Run as stand-alone process
            from src.worldstate import AntWorld
            bot = bots[0](AntWorld())
            bot._run()
          
    except KeyboardInterrupt:
        print('ctrl-c, leaving ...')

