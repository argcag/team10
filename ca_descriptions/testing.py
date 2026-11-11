import importlib.util
from pathlib import Path

import numpy as np

#python -m pytest testing.py -v
#load ca_descriptions/main.py
here = Path(__file__).resolve().parent
path = next(p / "ca_descriptions" / "main.py" for p in [here, *here.parents]
            if (p / "ca_descriptions" / "main.py").exists())
spec = importlib.util.spec_from_file_location("file", path)
file = importlib.util.module_from_spec(spec)
spec.loader.exec_module(file)


def test_fire_spreads_to_neighbours_but_no_wraparound(monkeypatch):
    #ignition chances guaranteed (when appropriate)[cha, lak, gra, for, bng, bnt]
    monkeypatch.setattr(file, "P_SPREAD", np.array([1.0, 0.0, 1.0, 1.0, 0.0, 0.0]))

    #5x5 chap with one fire on left edge
    grid = np.full((5, 5), file.CHAPARRAL)
    file.build_terrain(grid)
    grid[2, 0] = file.BURNING
    file.BURN_LEFT[2, 0] = file.BURN_TIME[file.CHAPARRAL]

    file.transition_func(grid, None, None)

    assert (grid[1:4, 1] == file.BURNING).all()      # spread to real neighbours
    assert (grid[:, 4] == file.CHAPARRAL).all()      # nothing on the opposite edge

def test_burning_cells_burn_out_after_burn_time(monkeypatch):
    #ignition chances guaranteed (when appropriate)[cha, lak, gra, for, bng, bnt]
    monkeypatch.setattr(file, "P_SPREAD", np.array([1.0, 0.0, 1.0, 1.0, 0.0, 0.0]))

    #5x5 chap with one fire on left edge
    grid = np.full((5, 5), file.CHAPARRAL)
    file.build_terrain(grid)
    grid[2, 2] = file.BURNING
    file.BURN_LEFT[2, 2] = file.BURN_TIME[file.CHAPARRAL]

    for _ in range(file.BURN_TIME[file.CHAPARRAL]):
        file.transition_func(grid, None, None)

    assert (grid[2, 2] == file.BURNT)

def test_town_burning_and_burnt_generations(monkeypatch):
    #ignition chances guaranteed (when appropriate)[cha, lak, gra, for, bng, bnt]
    monkeypatch.setattr(file, "P_SPREAD", np.array([1.0, 0.0, 1.0, 1.0, 0.0, 0.0]))

    #5x5 chap with one fire on left edge
    grid = np.full((5, 5), file.CHAPARRAL)
    file.build_terrain(grid)
    grid[2, 2] = file.BURNING
    file.BURN_LEFT[2, 2] = file.BURN_TIME[file.CHAPARRAL]
    file.TOWN = (slice(1, 4), slice(1, 4)) #index 1/2/3 by 1/2/3 (center 9 tiles)
    #define town in center of grid for testing.
    #not necessarily accurate as town is not usually 9/25 tiles.

    #reset town generations
    file.TOWN_BURNING_GENERATION = None
    file.TOWN_BURNT_GENERATION = None

    for _ in range(10):
        file.transition_func(grid, None, None)

    assert file.TOWN_BURNING_GENERATION is not None
    assert file.TOWN_BURNT_GENERATION is not None

def test_burn_left_decrements(monkeypatch):
    #ignition chances guaranteed (when appropriate)[cha, lak, gra, for, bng, bnt]
    monkeypatch.setattr(file, "P_SPREAD", np.array([1.0, 0.0, 1.0, 1.0, 0.0, 0.0]))

    #5x5 chap with one fire on left edge
    grid = np.full((5, 5), file.CHAPARRAL)
    file.build_terrain(grid)
    grid[2, 2] = file.BURNING
    file.BURN_LEFT[2, 2] = file.BURN_TIME[file.CHAPARRAL]

    initial_burn_left = file.BURN_LEFT[2, 2]

    file.transition_func(grid, None, None)

    assert file.BURN_LEFT[2, 2] == initial_burn_left - 1

def test_burn_left_does_not_decrement_for_non_burning_cells(monkeypatch):
    #ignition chances guaranteed (when appropriate)[cha, lak, gra, for, bng, bnt]
    monkeypatch.setattr(file, "P_SPREAD", np.array([1.0, 0.0, 1.0, 1.0, 0.0, 0.0]))

    #5x5 chap with one fire on left edge
    grid = np.full((5, 5), file.CHAPARRAL)
    file.build_terrain(grid)
    grid[2, 2] = file.BURNING
    file.BURN_LEFT[2, 2] = file.BURN_TIME[file.CHAPARRAL]

    initial_burn_left = file.BURN_LEFT[1, 1]  #non-burning cell

    file.transition_func(grid, None, None)

    assert file.BURN_LEFT[1, 1] == initial_burn_left

def test_burn_left_does_not_decrement_for_burnt_cells(monkeypatch):
    #ignition chances guaranteed (when appropriate)[cha, lak, gra, for, bng, bnt]
    monkeypatch.setattr(file, "P_SPREAD", np.array([1.0, 0.0, 1.0, 1.0, 0.0, 0.0]))

    #5x5 chap with one fire on left edge
    grid = np.full((5, 5), file.CHAPARRAL)
    file.build_terrain(grid)
    grid[2, 2] = file.BURNING
    file.BURN_LEFT[2, 2] = file.BURN_TIME[file.CHAPARRAL]

    #cell becomes BURNT
    for _ in range(file.BURN_TIME[file.CHAPARRAL]):
        file.transition_func(grid, None, None)

    initial_burn_left = file.BURN_LEFT[2, 2]  #burnt cell

    file.transition_func(grid, None, None)

    assert file.BURN_LEFT[2, 2] == initial_burn_left