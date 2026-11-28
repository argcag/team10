import contextlib
import importlib.util
import io
from pathlib import Path
from types import SimpleNamespace

import numpy as np

#note: this ignores wind so use set CA_WIND=S/N/NW/SE etc in cmd to test wind.
STRATEGIES = ["NONE", "TOWN_SURROUND", "SINGLE_BLOCK", "TWO_LINES", "ACTIVE_FRONT"]
RUNS = 20              #repeats per location
#load ca file (no gui)
path = Path(__file__).resolve().parent / "ca_descriptions" / "main.py"
spec = importlib.util.spec_from_file_location("ca", path)
ca = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ca)
ca.utils.load = lambda config_path: SimpleNamespace()   #fake capyle config

def run(strategy, seed):
    #One simulation. Returns gen that town first burns (300 if never).
    np.random.seed(seed)
    with contextlib.redirect_stdout(io.StringIO()):      #hide the cas own prints
        grid = ca.setup(["unused"]).initial_grid.copy()
        ca.WATER_STRATEGY = strategy
        ca.WATER_USED = 0                              #(generation, row, col) or None
        for generation in range(1, 300 + 1):
            ca.transition_func(grid, None, None)
            town = grid[ca.TOWN]
            if (town == ca.BURNING).any() or (town == ca.BURNT).any():      #burning or burnt for town
                return generation
    return None


for strategy in STRATEGIES:
    times = [run(strategy, seed) for seed in range(RUNS)]
    hit = [t for t in times if t is not None]
    average = "generation " + str(int(np.mean(hit))) if hit else "never"
    print(strategy + " town burns in " + str(len(hit)) + "/" + str(RUNS) + " runs, on average at " + average)

