#!/usr/bin/env python
import subprocess as sub
import numpy
import re

# Example helper script for running a series of games and computing
# some simple statistics of the ant bot scores.

num_trials = 10

# Location of the ants aichallenge directory.
base_dir = '/home/jengi/workspace/Ants/src/ants/aichallenge/ants/'

# Location of each bot's code.
bot_base = '"python ' + base_dir
bot1 = bot_base + '../../base/dfabot.py" '
bot2 = bot1
bot3 = bot_base + '../../base/greedybot.py" '
bot4 = bot3

# Parameters for the game playing.
command = base_dir + 'playgame.py --nolaunch --player_seed 42 --end_wait=0.25 --verbose --log_dir game_logs --turns 1000 --map_file ' + base_dir+ 'maps/symmetric_maps/symmetric_10.map "$@" ' + bot1 + bot2 + bot3 + bot4
score_pattern = re.compile('score(\s+\d+)(\s+\d+)(\s+\d+)(\s+\d+)')

# The score for each bot will be appended to its list each trial.
scores = {}
for i in range(0, 4):
    scores[i] = []

for i in range(0, num_trials):
    # Try to run one game and capture standard out/err. 
    process = sub.Popen(command, shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
    output, errors = process.communicate()

    # Exit on error.
    if errors:
        print errors
        exit

    # Record scores.
    match = score_pattern.search(output)
    print match.group(0)
    for i in range(0, 4):
        scores[i].append(int(match.group(i + 1)))

# Print summary statistics.
print '\n\t\t\taverage (standard deviation)'
for i in range(0, 4):
    print('Bot ' + str(i) + ':\t' + str(numpy.average(scores[i])) + 
          ' (' + str(numpy.std(scores[i])) + ')')
