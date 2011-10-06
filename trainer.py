'''
Created on Oct 1, 2011

@author: djweiss
'''

from src.batchlocalengine import BatchLocalEngine
from greedybot import GreedyBot
from src.features import FeatureExtractor, MovingTowardsFeatures
from valuebot import ValueBot
import random

def win_rate(bot_wins, bot_games):
    
    win_rate = [(i, float(bot_wins[i]) / float(bot_games[i])) for i in range(0, len(bot_wins))]
    win_rate.sort(key=lambda x: x[1], reverse=True)
    
    return win_rate

if __name__ == '__main__':
    engine = BatchLocalEngine()

    # Run quick games: 100 turns only
    engine.PrepareGame(["--run", "-t", "100"])
    
    # Generate a population of 30 random bots.
    features = FeatureExtractor.create(MovingTowardsFeatures.type_name)
    
    # Initialize a random set of bots
    team_a = [ValueBot(engine.GetWorld(), load_file=None) for i in range(5)]
    for bot in team_a:
        w = [random.uniform(-1,1) for i in range(0, features.num_features())]
        bot.set_features(features)        
        bot.set_weights(w)
        
    # Play several games against GreedyBot
    team_b = [GreedyBot(engine.GetWorld())]
    (bot_scores, bot_wins, bot_games) = engine.RunTournament(5, team_a, [GreedyBot(engine.GetWorld())], [30, 30])

    # Sort bots by their win rate
    a_rate = win_rate(bot_wins[0], bot_games[0])
    
    # Print out tournament results
    for i, rate in a_rate:
        print "Bot %d: Win rate = %g " % (i, rate)
        print team_a[i]
        team_a[i].save("saved_bots/bot_%d.json" % i)
    
    