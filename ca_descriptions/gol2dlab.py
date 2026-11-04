# Name: Conway's game of life
# Dimensions: 2
#conda activate COM3524
#python main.py
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
    # dead = state == 0, live = state == 1, sick = state == 2
    # unpack state counts for state 0, 1, and 2
    dead_neighbours, live_neighbours, sick_neighbours = neighbourcounts
    # create boolean arrays for the birth & survival rules
    # if 3 live/ sick neighbours and is dead -> cell born
    birth = ((live_neighbours + sick_neighbours) == 3) & (grid == 0)
    # if 2 or 3 live neighbours and is alive -> survives
    survive = ((live_neighbours == 2) | (live_neighbours == 3)) & (grid == 1)
    #become sick if more than 2 neighbours are sick and is alive
    become_sick = (sick_neighbours > 2) & (grid == 1)
    #remain sick if 1-4 sick neighbours and is sick
    remain_sick = (sick_neighbours > 0) & (sick_neighbours <= 4) & (grid == 2)
    #death from isolation if 0 or 1 neighbours are alive
    death_from_isolation = ((live_neighbours + sick_neighbours) <= 1) & (grid != 0)
    #death from sickness if sick and >4 neighbours are sick
    death_from_sickness = (sick_neighbours > 4) & (grid == 2)
    #recover if sick and no sick neighbours
    recovery = (sick_neighbours == 0) & (grid == 2)
    # Set all cells to 0 (dead)
    grid[:, :] = 0
    # Set cells to 1 where either cell is born or survives
    grid[birth | survive] = 1
    # Set cells to 2 where cell becomes or remains sick
    grid[become_sick | remain_sick] = 2
    # Set cells to 1 where cell recovers
    grid[recovery] = 1
    #set cells to 0 where cell dies
    grid[death_from_isolation | death_from_sickness] = 0
    return grid


def setup(args):
    config_path = args[0]
    config = utils.load(config_path)
    # ---THE CA MUST BE RELOADED IN THE GUI IF ANY OF THE BELOW ARE CHANGED---
    config.title = "Conway's game of life"
    config.dimensions = 2
    config.states = (0, 1, 2)
    # ------------------------------------------------------------------------

    # ---- Override the defaults below (these may be changed at anytime) ----

    config.state_colors = [(0,0,0),(1,1,1), (1,0,0)]
    # config.num_generations = 150
    # config.grid_dims = (200,200)
    config.initial_grid = np.random.choice([0, 1, 2], size=config.grid_dims, p=[0.6, 0.35, 0.05])

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
