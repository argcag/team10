import importlib.util
from pathlib import Path

import numpy as np

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