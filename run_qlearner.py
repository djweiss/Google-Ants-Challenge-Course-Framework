#!/usr/bin/env python
import subprocess as sub

# Loop qlearner, feeding in a new game number each iteration.
num_games = 50
command = "python qlearner.py"
for i in range(num_games):

    # Try to run one game and capture standard out/err. 
    current_command = command + " " + str(i)
    print 'Executing ' + current_command + " ..."
    process = sub.Popen(current_command, shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
    output, errors = process.communicate()
    print output
    print errors

