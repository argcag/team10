# Name: Wildfire modelling
# Dimensions: 2

# --- Set up executable path, do not edit ---
import sys
import inspect
this_file_loc = (inspect.stack()[0][1])
main_dir_loc = this_file_loc[:this_file_loc.index('ca_descriptions')]
sys.path.append(main_dir_loc)
sys.path.append(main_dir_loc + 'capyle')
sys.path.append(main_dir_loc + 'capyle/ca')
sys.path.append(main_dir_loc + 'capyle/guicomponents')
# ---

import os
from capyle.ca import Grid2D, Neighbourhood, CAConfig, randomise2d
import capyle.utils as utils
import numpy as np

CHAPARRAL, LAKE, GRASS, FOREST, BURNING, BURNT, TOWN_STATE = 0, 1, 2, 3, 4, 5, 6

#for determining what generation the town is burnt/burning
GENERATION = 0
TOWN = (slice(88, 92), slice(38, 42))
TOWN_BURNING_GENERATION = None
TOWN_BURNT_GENERATION = None

#index by code so    cha  lak  gra  for  bng  bnt  twn
P_SPREAD = np.array([0.5, 0.0, 0.9, 0.1, 0.0, 0.0, 0.5])
BURN_TIME = np.array([3,   0,   1,  30,  0,   0,   5]) 

#wind configuration
WIND_KERNELS = {
    'NONE': np.array([[1.0, 1.0, 1.0],
                      [1.0, 0.0, 1.0],
                      [1.0, 1.0, 1.0]]),
    'SE':   np.array([[1.30, 0.85, 0.40],
                      [0.85, 0.0,  0.20],
                      [0.40, 0.20, 0.15]]),
    'S':    np.array([[0.85, 1.30, 0.85],
                      [0.40, 0.0,  0.40],
                      [0.20, 0.15, 0.20]]),
    'E':    np.array([[0.85, 0.40, 0.20],
                      [1.30, 0.0,  0.15],
                      [0.85, 0.40, 0.20]]),
    'N':    np.array([[0.20, 0.15, 0.20],
                      [0.40, 0.0,  0.40],
                      [0.85, 1.30, 0.85]]),
    'W':    np.array([[0.20, 0.40, 0.85],
                      [0.15, 0.0,  1.30],
                      [0.20, 0.40, 0.85]]),
    'NE':   np.array([[0.40, 0.20, 0.15],
                      [0.85, 0.0,  0.20],
                      [1.30, 0.85, 0.40]]),
    'SW':   np.array([[0.40, 0.85, 1.30],
                      [0.20, 0.0,  0.85],
                      [0.15, 0.20, 0.40]]),
    'NW':   np.array([[0.15, 0.20, 0.40],
                      [0.20, 0.0,  0.85],
                      [0.40, 0.85, 1.30]]),
}

WIND_DIRECTION = os.environ.get("CA_WIND", "SE")


TERRAIN = None #original terrain of each cell
BURN_LEFT = None #days of burning remaining (per cell)
#water dropping
#DROP_AT = None      #(gen row col)
DROP_AT = (90, 85, 45)
WET_TIME = 50        #steps a soaked cell can't ignite
WETNESS = None      #steps of protection left, per cell
DROP_SIZE = 7       #cells per side (odd number). 7 x 7 = 49 cells = 12.25 km^2 (close enough to 12.5)

def apply_drop(grid): #apply water drop
    _, row, col = DROP_AT                    #centre of the drop
    half = DROP_SIZE // 2
    area = (slice(max(row - half, 0), row + half + 1),
            slice(max(col - half, 0), col + half + 1))
    WETNESS[area] = WET_TIME
    grid[area][grid[area] == BURNING] = BURNT

def transition_func(grid, neighbourstates, neighbourcounts):
    #count gens so it can be printed in command line when town is affected.
    global GENERATION, TOWN_BURNING_GENERATION, TOWN_BURNT_GENERATION
    GENERATION += 1
    if DROP_AT is not None and GENERATION == DROP_AT[0]:
        apply_drop(grid)
    #had to alter burning neighbours calculation so that fire doesnt wrap around to the other
    #side of the grid (fire should not spread like that)
    #weighted burning neighbours using wind kernel
    w = WIND_KERNELS[WIND_DIRECTION]
    b = np.pad(grid == BURNING, 1).astype(float)
    
    burning_neighbours = (
            w[0,0]*b[:-2, :-2] + w[0,1]*b[:-2, 1:-1] + w[0,2]*b[:-2, 2:] +
            w[1,0]*b[1:-1, :-2]                      + w[1,2]*b[1:-1, 2:] +
            w[2,0]*b[2:, :-2]  + w[2,1]*b[2:, 1:-1]  + w[2,2]*b[2:, 2:]
        )    
    flammable_cells = (grid == 0) | (grid == 2) | (grid == 3) | (grid == 6)  #all unburnt but lake are flammable
    rand1 = np.random.random(grid.shape)
    #catching fire 
    catch_fire = 1 - (1 - P_SPREAD[TERRAIN])**burning_neighbours
    on_fire = flammable_cells & (rand1 < catch_fire) & (WETNESS == 0)
    WETNESS[WETNESS > 0] -= 1
    #burning out
    burning = (grid == BURNING)
    BURN_LEFT[burning] -= 1
    burn_out = burning & (BURN_LEFT <= 0)
    #set grid
    grid[on_fire] = BURNING
    grid[burn_out] = BURNT
    #print when town is burning or burnt
    town = grid[TOWN]
    if TOWN_BURNING_GENERATION is None and (town == BURNING).any():
        TOWN_BURNING_GENERATION = GENERATION
        print(f"[Generation {GENERATION}]: town is burning (Wind: {WIND_DIRECTION})", flush=True) #flush forces text output asap
    if TOWN_BURNT_GENERATION is None and (town == BURNT).any():
        TOWN_BURNT_GENERATION = GENERATION
        print(f"[Generation {GENERATION}]: town has burnt", flush=True)
    return grid

def build_terrain(grid):
    global TERRAIN, BURN_LEFT, WETNESS
    TERRAIN = np.zeros(grid.shape, dtype=int)
    BURN_LEFT = np.zeros(grid.shape, dtype=int)
    WETNESS = np.zeros(grid.shape, dtype=int)
    #set terrain types
    TERRAIN[grid == 0] = CHAPARRAL
    TERRAIN[grid == 1] = LAKE
    TERRAIN[grid == 2] = GRASS
    TERRAIN[grid == 3] = FOREST
    TERRAIN[grid == 4] = BURNING
    TERRAIN[grid == 5] = BURNT
    TERRAIN[grid == 6] = TOWN_STATE
    #set burn times
    BURN_LEFT[TERRAIN == CHAPARRAL] = BURN_TIME[CHAPARRAL]
    BURN_LEFT[TERRAIN == LAKE]     = BURN_TIME[LAKE]
    BURN_LEFT[TERRAIN == GRASS]    = BURN_TIME[GRASS]
    BURN_LEFT[TERRAIN == FOREST]   = BURN_TIME[FOREST]
    BURN_LEFT[TERRAIN == BURNING]  = BURN_TIME[BURNING]
    BURN_LEFT[TERRAIN == BURNT]    = BURN_TIME[BURNT]
    BURN_LEFT[TERRAIN == TOWN_STATE] = BURN_TIME[TOWN_STATE]

def setup(args):
    global GENERATION, TOWN_BURNING_GENERATION, TOWN_BURNT_GENERATION
    GENERATION = 0
    TOWN_BURNING_GENERATION = None
    TOWN_BURNT_GENERATION = None
    config_path = args[0]
    config = utils.load(config_path)
    # ---THE CA MUST BE RELOADED IN THE GUI IF ANY OF THE BELOW ARE CHANGED---
    config.title = "Wildfire modelling"
    config.dimensions = 2
    config.states = (0, 1, 2, 3, 4, 5, 6)
    # ------------------------------------------------------------------------

    # ---- Override the defaults below (these may be changed at anytime) ----
    #unburnt = green, burning = red, burnt = gray
    config.state_colors = [
        (0.45, 0.55, 0.20), #chap greeny yellow
        (0.20, 0.40, 0.80), #lake blue
        (0.90, 0.85, 0.40), #grass kinda yellow
        (0.2, 0.6, 0.2),    #forest dark green
        (1, 0.4, 0),        #burning orange
        (0.15, 0.15, 0.15), #burnt dark gray
        (0, 0, 0)]          #black (town)
    config.num_generations = 300 #represents 300 days
    config.grid_dims = (100,100) # 1 cell = 0.5km so grid is 50x50km
    #randomised (for testing)
    #config.initial_grid = np.random.choice([0, 1, 2], size=config.grid_dims, p=[0.6, 0.35, 0.05])
    grid = np.full(config.grid_dims, CHAPARRAL, dtype=int)
    grid[10:14, 0:50] = FOREST #matches spec of assignment instructions doc
    grid[14:60, 10:25] = FOREST
    grid[60:70, 10:50] = FOREST
    grid[20:30, 64:90] = FOREST
    grid[88:92, 38:42] = TOWN_STATE

    grid[24:45, 35:45] = LAKE
    grid[55:80, 75:80] = LAKE

    grid[45:50, 50:90] = GRASS

    build_terrain(grid) #store terrain before adding fire
    grid[(slice(0, 2), slice(0, 2))] = BURNING
    BURN_LEFT[(slice(0, 2), slice(0, 2))] = BURN_TIME[TERRAIN[(slice(0, 2), slice(0, 2))]] #burn time for initial fire
    config.initial_grid = grid.copy()
    # ----------------------------------------------------------------------

    if len(args) == 2:
        config.save()
        sys.exit()

    return config


def main():
    global WIND_DIRECTION, GENERATION, TOWN_BURNING_GENERATION, TOWN_BURNT_GENERATION
    # Open the config object
    config = setup(sys.argv[1:])

    # Guarantee fresh counters on every Run
    GENERATION = 0
    TOWN_BURNING_GENERATION = None
    TOWN_BURNT_GENERATION = None

    #read wind direction selected in CAPyle drop down menu
    WIND_DIRECTION = os.environ.get("CA_WIND", "SE")
    print(f"Running simulation with global wind: {WIND_DIRECTION}", flush=True)

    # Create grid object
    grid = Grid2D(config, transition_func)

    # Run the CA, save grid state every generation to timeline
    timeline = grid.run()
    #if town doesnt catch fire print.
    if TOWN_BURNING_GENERATION is None:
        print(f"town never caught fire in {GENERATION} generations", flush=True)

    # save updated config to file
    config.save()
    # save timeline to file
    utils.save(timeline, config.timeline_path)


if __name__ == "__main__":
    main()
