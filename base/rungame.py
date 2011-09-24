import sys


#Main section allowing for dual use either with the standard engine
# or the LocalEngine. If no arguments are given, it calls
# AntsBot.Run() to run as a stand alone process, communicating via
# stdin/stdout. However, if arguments are given, it passes them to
# LocalEngine and creates two instances of GreedyBot to play against
# one another.
if __name__ == '__main__':
  # From Ants distribution: use psyco to speed up all code.
  print sys.argv
  try:
    import psyco
    psyco.full()
  except ImportError:
    pass

  try:
    #-3 here is to cut of .py, which is not used in imports
    Red = __import__(sys.argv[1][:-3]).BOT
    if len(sys.argv) > 2: # Run LocalEngine version
      Blue = __import__(sys.argv[2][:-3]).BOT
      from src.localengine import LocalEngine
      engine = LocalEngine()
      engine.AddBot(Red(engine.GetWorld()))
      engine.AddBot(Blue(engine.GetWorld()))
      del sys.argv[1]
      del sys.argv[1]
      engine.Run(sys.argv)
    else: # Run as stand-alone process
      bot = Red(AntWorld())
      bot._run()
  except KeyboardInterrupt:
      print('ctrl-c, leaving ...')

