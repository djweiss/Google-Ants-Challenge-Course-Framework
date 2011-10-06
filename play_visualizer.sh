#!/usr/bin/env sh

# Generate a random 2 player map to play on with dims between 20 and 80 
python src/mapgen.py -n 2 -l 30 -u 80 > src/maps/2player/tmp_random.map

# Run the playgame script.
python aic-sim/playgame.py --log_dir game_logs -E -O --turns 1500 --verbose \
    -m src/maps/2player/tmp_random.map \
    "python rungame.py $1" \
    "python rungame.py $2"