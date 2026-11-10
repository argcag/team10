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

from capyle.ca import Grid2D, Neighbourhood, CAConfig, randomise2d
import capyle.utils as utils
import numpy as np

CHAPARRAL, LAKE, GRASS, FOREST, BURNING, BURNT = 0, 1, 2, 3, 4, 5

#for determining what generation the town is burnt/burning
GENERATION = 0
TOWN = (slice(88, 92), slice(38, 42))
TOWN_BURNING_GENERATION = None
TOWN_BURNT_GENERATION = None

#index by code so    cha  lak  gra  for  bng  bnt
P_SPREAD = np.array([0.5, 0.0, 0.9, 0.1, 0.0, 0.0])
BURN_TIME = np.array([3,   0,   1,  30,  0,   0]) 

TERRAIN = None #original terrain of each cell
BURN_LEFT = None #days of burning remaining (per cell)

def transition_func(grid, neighbourstates, neighbourcounts):
    #count gens so it can be printed in command line when town is affected.
    global GENERATION, TOWN_BURNING_GENERATION, TOWN_BURNT_GENERATION
    GENERATION += 1
    
    #had to alter burning neighbours calculation so that fire doesnt wrap around to the other
    #side of the grid (fire should not spread like that)
    b = np.pad(grid == BURNING, 1).astype(int)
    burning_neighbours = (b[:-2, :-2] + b[:-2, 1:-1] + b[:-2, 2:] + b[1:-1, :-2] + b[1:-1, 2:] + b[2:, :-2] + b[2:, 1:-1] + b[2:, 2:])
    flammable_cells = (grid == 0) | (grid == 2) | (grid == 3) #all unburnt but lake are flammable
    rand1 = np.random.random(grid.shape)
    #catching fire 
    catch_fire = 1 - (1 - P_SPREAD[TERRAIN])**burning_neighbours
    on_fire = flammable_cells & (rand1 < catch_fire)
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
        print(f"[Generation {GENERATION}]: town is burning", flush=True) #flush forces text output asap
    if TOWN_BURNT_GENERATION is None and (town == BURNT).any():
        TOWN_BURNT_GENERATION = GENERATION
        print(f"[Generation {GENERATION}]: town has burnt", flush=True)
    return grid

def build_terrain(grid):
    global TERRAIN, BURN_LEFT
    TERRAIN = np.zeros(grid.shape, dtype=int)
    BURN_LEFT = np.zeros(grid.shape, dtype=int)
    #set terrain types
    TERRAIN[grid == 0] = CHAPARRAL
    TERRAIN[grid == 1] = LAKE
    TERRAIN[grid == 2] = GRASS
    TERRAIN[grid == 3] = FOREST
    TERRAIN[grid == 4] = BURNING
    TERRAIN[grid == 5] = BURNT
    #set burn times
    BURN_LEFT[TERRAIN == CHAPARRAL] = BURN_TIME[CHAPARRAL]
    BURN_LEFT[TERRAIN == LAKE]     = BURN_TIME[LAKE]
    BURN_LEFT[TERRAIN == GRASS]    = BURN_TIME[GRASS]
    BURN_LEFT[TERRAIN == FOREST]   = BURN_TIME[FOREST]
    BURN_LEFT[TERRAIN == BURNING]  = BURN_TIME[BURNING]
    BURN_LEFT[TERRAIN == BURNT]    = BURN_TIME[BURNT]

def setup(args):
    config_path = args[0]
    config = utils.load(config_path)
    # ---THE CA MUST BE RELOADED IN THE GUI IF ANY OF THE BELOW ARE CHANGED---
    config.title = "Wildfire modelling"
    config.dimensions = 2
    config.states = (0, 1, 2, 3, 4, 5)
    # ------------------------------------------------------------------------

    # ---- Override the defaults below (these may be changed at anytime) ----
    #unburnt = green, burning = red, burnt = gray
    config.state_colors = [
        (0.45, 0.55, 0.20), #chap greeny yellow
        (0.20, 0.40, 0.80), #lake blue
        (0.90, 0.85, 0.40), #grass kinda yellow
        (0.2, 0.6, 0.2),    #forest dark green
        (1, 0.4, 0),        #burning orange
        (0.15, 0.15, 0.15)] #burnt dark gray
    config.num_generations = 300 #represents 300 days
    config.grid_dims = (100,100) # 1 cell = 0.5km so grid is 50x50km
    #randomised (for testing)
    #config.initial_grid = np.random.choice([0, 1, 2], size=config.grid_dims, p=[0.6, 0.35, 0.05])
    grid = np.full(config.grid_dims, CHAPARRAL, dtype=int)
    grid[10:14, 0:50] = FOREST #matches spec of assignment instructions doc
    grid[14:60, 10:25] = FOREST
    grid[60:70, 10:50] = FOREST
    grid[20:30, 64:90] = FOREST

    grid[24:45, 35:45] = LAKE
    grid[55:80, 75:80] = LAKE

    grid[45:50, 50:90] = GRASS

    build_terrain(grid) #store terrain before adding fire
    grid[(slice(0, 2), slice(0, 2))] = BURNING
    BURN_LEFT[(slice(0, 2), slice(0, 2))] = BURN_TIME[TERRAIN[(slice(0, 2), slice(0, 2))]] #burn time for initial fire
    config.initial_grid = grid
    # ----------------------------------------------------------------------

    if len(args) == 2:
        config.save()
        sys.exit()

    return config


def main():
    # Open the config object
    config = setup(sys.argv[1:])

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
