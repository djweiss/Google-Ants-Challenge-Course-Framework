#!/usr/bin/env python
# Created: September 2011
# Author: David Weiss
#
# A small stub that will be run when you submit 
# your code to the Competition Server.

from worldstate import AntWorld

### CHANGE THIS TO IMPORT THE BOT YOU'D LIKE TO RUN.
from dfabot import DFABot
bot = DFABot(AntWorld())

bot._run()
