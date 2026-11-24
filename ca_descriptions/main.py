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

CHAPARRAL, LAKE, GRASS, FOREST, BURNING, BURNT, TOWN_STATE, MARSH, GRAZED_CHAPARRAL, GRAZED_GRASS, MOIST_CHAPARRAL, MOIST_GRASS, MOIST_FOREST, MOIST_TOWN, MOIST_GRAZED_CHAPARRAL, MOIST_GRAZED_GRASS = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15
(MOIST_CHAPARRAL, MOIST_GRASS, MOIST_FOREST, MOIST_TOWN,
 MOIST_GRAZED_CHAPARRAL, MOIST_GRAZED_GRASS) = range(10, 16)

DRY_SOAKABLE_STATES = (CHAPARRAL, GRASS, FOREST, TOWN_STATE, GRAZED_CHAPARRAL, GRAZED_GRASS)
MOIST_STATES = (MOIST_CHAPARRAL, MOIST_GRASS, MOIST_FOREST, MOIST_TOWN, MOIST_GRAZED_CHAPARRAL, MOIST_GRAZED_GRASS)
UNBURNT_STATES = DRY_SOAKABLE_STATES + (MARSH,) + MOIST_STATES

# Map any state ID to its moist variant (lake and marsh map to themselves)
# Index:             0                1     2            3             4        5      6           7      8                       9                   10               11           12            13          14                      15
TO_MOIST = np.array([MOIST_CHAPARRAL, LAKE, MOIST_GRASS, MOIST_FOREST, BURNING, BURNT, MOIST_TOWN, MARSH, MOIST_GRAZED_CHAPARRAL, MOIST_GRAZED_GRASS, MOIST_CHAPARRAL, MOIST_GRASS, MOIST_FOREST, MOIST_TOWN, MOIST_GRAZED_CHAPARRAL, MOIST_GRAZED_GRASS])

#for determining what generation the town is burnt/burning
GENERATION = 0
TOWN = (slice(88, 92), slice(38, 42))
TOWN_BURNING_GENERATION = None
TOWN_BURNT_GENERATION = None
FIRE_END_GENERATION = None

#index by code so    cha  lak  gra  for  bng  bnt  twn   wet    mar  gch  ggr
P_SPREAD  = np.array([0.50, 0.0, 0.90, 0.10, 0.0, 0.0, 0.50, 0.15, 0.12, 0.20, 0.05, 0.08, 0.01, 0.05, 0.01, 0.02])
BURN_TIME = np.array([3,    0,   1,    30,   0,   0,   5,    2,    1,    1,    2,    1,    20,   3,    1,    1])

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

ANIMALS_PER_CELL = 25
GRAZING_ANIMALS = int(os.environ.get("CA_GRAZING_ANIMALS", "0"))

TERRAIN = None #original terrain of each cell
BURN_LEFT = None #days of burning remaining (per cell)
#water dropping
#DROP_AT = None      #(gen row col)
MAX_DROP_CELLS = 50
WATER_USED = 0
WET_TIME = 50
WETNESS = None
WATER_STRATEGY = os.environ.get("CA_WATER_STRATEGY", "TOWN_SURROUND")


def soak_cells(grid, rows, cols):
    """Apply water to specific (row, col) coordinates up to MAX_DROP_CELLS."""
    global WATER_USED
    remaining = MAX_DROP_CELLS - WATER_USED
    if remaining <= 0 or len(rows) == 0:
        return

    rows = np.asarray(rows)[:remaining]
    cols = np.asarray(cols)[:remaining]
    WATER_USED += len(rows)

    for r, c in zip(rows, cols):
        if grid[r, c] == BURNING:
            grid[r, c] = BURNT
        elif int(grid[r, c]) in DRY_SOAKABLE_STATES or int(grid[r, c]) in MOIST_STATES:
            grid[r, c] = TO_MOIST[TERRAIN[r, c]]
            WETNESS[r, c] = WET_TIME


def drop_town_surround(grid):
    """protective ring around TOWN with extra in upwind corner cells."""
    mask = np.zeros(grid.shape, dtype=bool)
    mask[86:94, 36:44] = True
    mask[88:92, 38:42] = False  # exclude town interior (64 - 16 = 48 cells)
    mask[85, 36:38] = True      # +2 upwind NW cells = 50 cells total
    rows, cols = np.where(mask)
    soak_cells(grid, rows, cols)


def drop_single_block(grid):
    """single 7x7 block upwind of town."""
    rows, cols = np.meshgrid(np.arange(82, 89), np.arange(32, 39), indexing='ij')
    soak_cells(grid, rows.ravel(), cols.ravel())


def drop_two_lines(grid, row_start, col_start):
    """2 horizontal firebreak lines."""
    rows = np.full(25, row_start)
    cols = np.arange(col_start, col_start + 25)
    soak_cells(grid, rows, cols)


def drop_active_front(grid, max_cells=25):
    """2 lines targeting burning cells closest to the town."""
    b_rows, b_cols = np.where(grid == BURNING)
    if len(b_rows) == 0:
        return
    dist_sq = (b_rows - 90) ** 2 + (b_cols - 40) ** 2
    nearest = np.argsort(dist_sq)[:max_cells]
    soak_cells(grid, b_rows[nearest], b_cols[nearest])


def apply_water_strategy(grid):
    if WATER_STRATEGY == "NONE":
        return
    elif WATER_STRATEGY == "TOWN_SURROUND" and GENERATION == 60:
        drop_town_surround(grid)
    elif WATER_STRATEGY == "SINGLE_BLOCK" and GENERATION == 90:
        drop_single_block(grid)
    elif WATER_STRATEGY == "TWO_LINES":
        if GENERATION == 45:
            drop_two_lines(grid, row_start=52, col_start=25)
        elif GENERATION == 80:
            drop_two_lines(grid, row_start=84, col_start=28)
    elif WATER_STRATEGY == "ACTIVE_FRONT" and GENERATION in (65, 95):
        drop_active_front(grid, max_cells=25)

PREBURN_STRATEGY = os.environ.get("CA_PREBURN_STRATEGY", "NONE")
PREBURNABLE_STATES = (CHAPARRAL, GRASS, GRAZED_CHAPARRAL, GRAZED_GRASS)

def apply_preburn(grid, strategy):
    #Create 2 cell wide pre-burned firebreaks before ignition
    if strategy == "NONE":
        return

    mask = np.zeros(grid.shape, dtype=bool)

    if strategy in ("TOWN_PERIMETER", "FULL_NETWORK"):
        #protective ring around the town
        mask[86:94, 36:44] = True
        mask[88:92, 38:42] = False

    if strategy in ("CORRIDOR_STRIP", "FULL_NETWORK"):
        #stepped fuel break across forest
        mask[72:74, 15:65] = True
        for i in range(12):
            mask[60 + i, 25 + i : 27 + i] = True

    if strategy == "FULL_NETWORK":
        #containment line below the upper forest
        mask[32:34, 46:74] = True

    # Only burn safe shrub/grassland fuels (never forest, town, marsh, or lake)
    valid_firebreak = mask & np.isin(grid, PREBURNABLE_STATES)
    grid[valid_firebreak] = BURNT

def transition_func(grid, neighbourstates, neighbourcounts):
    #count gens so it can be printed in command line when town is affected.
    global GENERATION, TOWN_BURNING_GENERATION, TOWN_BURNT_GENERATION, FIRE_END_GENERATION
    GENERATION += 1

    apply_water_strategy(grid)
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
    grid_int = grid.astype(int)
    flammable_cells = np.isin(grid_int, UNBURNT_STATES)
    rand1 = np.random.random(grid.shape)
    #catching fire (uses current grid state so moist variants have reduced spread)
    current_p_spread = np.where(flammable_cells, P_SPREAD[grid_int], 0.0)
    catch_fire = 1 - (1 - current_p_spread)**burning_neighbours
    on_fire = flammable_cells & (rand1 < catch_fire)
    BURN_LEFT[on_fire] = BURN_TIME[grid_int[on_fire]]

    WETNESS[WETNESS > 0] -= 1
    dried = np.isin(grid, MOIST_STATES) & (WETNESS == 0)
    grid[dried] = TERRAIN[dried]
    #burning out
    burning = (grid == BURNING)
    BURN_LEFT[burning] -= 1
    burn_out = burning & (BURN_LEFT <= 0)
    #set grid
    grid[on_fire] = BURNING
    grid[burn_out] = BURNT
    if FIRE_END_GENERATION is None and not (grid == BURNING).any():
        FIRE_END_GENERATION = GENERATION
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
    TERRAIN = grid.copy()
    BURN_LEFT = BURN_TIME[TERRAIN]
    WETNESS = np.zeros(grid.shape, dtype=int)

def setup(args):
    global GENERATION, TOWN_BURNING_GENERATION, TOWN_BURNT_GENERATION, FIRE_END_GENERATION
    GENERATION = 0
    TOWN_BURNING_GENERATION = None
    TOWN_BURNT_GENERATION = None
    FIRE_END_GENERATION = None
    GRAZING_ANIMALS = int(os.environ.get("CA_GRAZING_ANIMALS", "0"))
    PREBURN_STRATEGY = os.environ.get("CA_PREBURN_STRATEGY", "NONE")
    MARSH_ENABLED = os.environ.get("CA_MARSH_ENABLED", "0") == "0"
    config_path = args[0]
    config = utils.load(config_path)
    # ---THE CA MUST BE RELOADED IN THE GUI IF ANY OF THE BELOW ARE CHANGED---
    config.title = "Wildfire modelling"
    config.dimensions = 2
    config.states = tuple(range(16))
    # ------------------------------------------------------------------------

    config.state_colors = [
        (0.45, 0.55, 0.20), # 0: chaparral
        (0.20, 0.40, 0.80), # 1: lake
        (0.90, 0.85, 0.40), # 2: grass
        (0.20, 0.60, 0.20), # 3: forest
        (1.00, 0.40, 0.00), # 4: burning
        (0.15, 0.15, 0.15), # 5: burnt
        (0.00, 0.00, 0.00), # 6: town
        (0.30, 0.50, 0.45), # 7: marsh
        (0.65, 0.72, 0.40), # 8: grazed chaparral
        (0.95, 0.92, 0.65), # 9: grazed grass
        (0.35, 0.55, 0.45), # 10: moist chaparral
        (0.65, 0.80, 0.65), # 11: moist grass
        (0.15, 0.50, 0.45), # 12: moist forest
        (0.20, 0.30, 0.45), # 13: moist town
        (0.50, 0.68, 0.58), # 14: moist grazed chaparral
        (0.75, 0.88, 0.80), # 15: moist grazed grass
    ]
              
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

    if MARSH_ENABLED:
        grid[22:47, 33:47] = MARSH
        grid[53:82, 73:82] = MARSH

    grid[24:45, 35:45] = LAKE
    grid[55:80, 75:80] = LAKE

    grid[24:45, 35:45] = LAKE
    grid[55:80, 75:80] = LAKE

    if GRAZING_ANIMALS > 0:
            cells_to_graze = GRAZING_ANIMALS // ANIMALS_PER_CELL
            block_size = 5
            num_herds = max(1, cells_to_graze // (block_size * block_size))
            for _ in range(num_herds):
                r = np.random.randint(0, config.grid_dims[0] - block_size)
                c = np.random.randint(0, config.grid_dims[1] - block_size)
                patch = grid[r:r+block_size, c:c+block_size]
                patch[patch == CHAPARRAL] = GRAZED_CHAPARRAL
                patch[patch == GRASS] = GRAZED_GRASS

    apply_preburn(grid, PREBURN_STRATEGY)

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
    global WIND_DIRECTION, GENERATION, TOWN_BURNING_GENERATION, TOWN_BURNT_GENERATION, FIRE_END_GENERATION
    # Open the config object
    config = setup(sys.argv[1:])

    # Guarantee fresh counters on every Run
    GENERATION = 0
    TOWN_BURNING_GENERATION = None
    TOWN_BURNT_GENERATION = None
    FIRE_END_GENERATION = None

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

    # calculate wind metrics
    final_grid = timeline[-1]
    total_flammable = np.sum(TERRAIN != LAKE)
    total_affected = np.sum((final_grid == BURNT) | (final_grid == BURNING))
    pct_burnt = (total_affected / total_flammable) * 100

    fire_dur_str = str(FIRE_END_GENERATION) if FIRE_END_GENERATION is not None else f">{GENERATION} (Still burning)"
    print(
        f"Active Duration: {fire_dur_str} | "
        f"Flammable Burnt: {pct_burnt:.2f}%",
        flush=True
    )


    # save updated config to file
    config.save()
    # save timeline to file
    utils.save(timeline, config.timeline_path)


if __name__ == "__main__":
    main()
