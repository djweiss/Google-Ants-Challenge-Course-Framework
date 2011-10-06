#!/usr/bin/env python
# Created: September 2011
# Author: David Weiss
#
# A small stub that will be run when you submit 
# your code to the Competition Server.

from src.worldstate import AntWorld

### CHANGE THIS TO IMPORT FROM YOUR BOT FILE.
from valuebot import BOT

# Run the bot.
bot = BOT(AntWorld())
bot._run()
