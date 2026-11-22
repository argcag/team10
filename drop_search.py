import contextlib
import importlib.util
import io
from pathlib import Path
from types import SimpleNamespace

import numpy as np

#note: this ignores wind so use set CA_WIND=S/N/NW/SE etc in cmd to test wind.
DROP_GENERATION = 90   #generation the drop happens on
DROP_RADIUS = 10       #cells
WET_TIME = 50          #n of gens a soaked cell cant ignite for
RUNS = 10              #repeats per location
STEP = 10              #gap between candidate locations, in cells

#load ca file (no gui)
path = Path(__file__).resolve().parent / "ca_descriptions" / "main.py"
spec = importlib.util.spec_from_file_location("ca", path)
ca = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ca)
ca.utils.load = lambda config_path: SimpleNamespace()   #fake capyle config
ca.DROP_RADIUS = DROP_RADIUS
ca.WET_TIME = WET_TIME


def run(drop, seed):
    #One simulation. Returns gen that town first burns (300 if never).
    np.random.seed(seed)
    with contextlib.redirect_stdout(io.StringIO()):      #hide the cas own prints
        grid = ca.setup(["unused"]).initial_grid.copy()
        ca.GENERATION = 0
        ca.DROP_AT = drop                                #(generation, row, col) or None
        for generation in range(1, 300 + 1):
            ca.transition_func(grid, None, None)
            town = grid[ca.TOWN]
            if (town == ca.BURNING).any() or (town == ca.BURNT).any():      #burning or burnt for town
                return generation
    return 300


def average_town_time(drop): #avg town survival time over n of runs - seeds 0 -> runs-1
    total = 0
    for seed in range(RUNS):
        total += run(drop, seed)
    return total / RUNS


#no drop, town survival time
baseline = average_town_time(None) 
print("No drop: town catches fire at generation " + str(baseline) + " on average")
height, width = 100, 100

#drop on every location
results = []
for row in range(STEP // 2, height, STEP): #steps by 10 each time but on the 5s
    for col in range(STEP // 2, width, STEP): #steps by 10 each time but on the 5s
        results.append((average_town_time((DROP_GENERATION, row, col)), row, col))

#show results (longest until town burns wins)
results.sort(reverse=True)
print("Best 5 drop locations:")
for time_to_town, row, col in results[:5]:
    print(" row " + str(row) + ", col " + str(col) + ": town catches fire at generation " + str(time_to_town) + " on average")