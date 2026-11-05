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


def transition_func(grid, neighbourstates, neighbourcounts):
    # unharmed = state == 0, burning = state == 1, burnt = state == 2
    # unpack state counts for state 0, 1 and 2
    unharmed_neighbours, burning_neighbours, burnt_neighbours = neighbourcounts
    #chance of spread is 0.25 per neighbour.
    p_spread  = 0.25
    p_burnout = 0.2
    rand1 = np.random.random(grid.shape)
    rand2 = np.random.random(grid.shape)
    #catching fire 
    catch_fire = 1 - (1 - p_spread)**burning_neighbours
    on_fire = (grid == 0) & (rand1 < catch_fire)
    #burning out
    burn_out = (rand2 < p_burnout) & (grid == 1)
    #set grid
    grid[on_fire] = 1
    grid[burn_out] = 2
    return grid


def setup(args):
    config_path = args[0]
    config = utils.load(config_path)
    # ---THE CA MUST BE RELOADED IN THE GUI IF ANY OF THE BELOW ARE CHANGED---
    config.title = "Wildfire modelling"
    config.dimensions = 2
    config.states = (0, 1, 2)
    # ------------------------------------------------------------------------

    # ---- Override the defaults below (these may be changed at anytime) ----
    #unburnt = green, burning = red, burnt = gray
    config.state_colors = [(0.2, 0.6, 0.2),(1, 0.4, 0),(0.15, 0.15, 0.15)]
    # config.num_generations = 150
    config.grid_dims = (200,200)
    #randomised (for testing)
    #config.initial_grid = np.random.choice([0, 1, 2], size=config.grid_dims, p=[0.6, 0.35, 0.05])
    grid = np.zeros(config.grid_dims, dtype=int)
    grid[config.grid_dims[0]//2, config.grid_dims[1]//2] = 1
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

    # save updated config to file
    config.save()
    # save timeline to file
    utils.save(timeline, config.timeline_path)


if __name__ == "__main__":
    main()
