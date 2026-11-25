import tkinter as tk
import numpy as np
import os
from capyle.utils import gens_to_dims, alerterror, alertcontinue
from capyle.guicomponents import (_GenerationsUI, _GridDimensionsUI,
                                  _Separator, _NeighbourhoodUI, _RuleNumberUI,
                                  _StateColorsUI, _InitialGridUI)

class _ConfigFrame(tk.Frame):

    def __init__(self, parent, ca_config):
        tk.Frame.__init__(self, parent, padx=10)
        self.ca_config = ca_config
        self.ca_graph = None

        # Top row: Reset button on the left, Wind drop-down on the right
        top_frame = tk.Frame(self)
        top_frame.pack(fill=tk.BOTH)

        btn_reset = tk.Button(top_frame, text="Reset config",
                              command=self.reset)
        btn_reset.pack(side=tk.LEFT)

        self.wind_var = tk.StringVar(value=os.environ.get("CA_WIND", "SE"))
        os.environ["CA_WIND"] = self.wind_var.get()

        wind_menu = tk.OptionMenu(
            top_frame,
            self.wind_var,
            "NONE", "N", "NE", "E", "SE", "S", "SW", "W", "NW",
            command=lambda val: os.environ.__setitem__("CA_WIND", val)
        )
        wind_menu.pack(side=tk.RIGHT)
        tk.Label(top_frame, text="Wind:").pack(side=tk.RIGHT)

        self.burn_var = tk.StringVar(value=os.environ.get("CA_BURN_LOCATION", "Power Plant"))
        os.environ["CA_BURN_LOCATION"] = self.burn_var.get()

        burn_menu = tk.OptionMenu(
            top_frame,
            self.burn_var,
            "NONE", "Power Plant", "Incinerator",
            command=lambda val: os.environ.__setitem__("CA_BURN_LOCATION", val)
        )
        burn_menu.pack(side=tk.RIGHT)
        tk.Label(top_frame, text="Burn Location:").pack(side=tk.RIGHT)

        self.separator()

        # --- Group 1: Long-Term Prevention (Grazing & Prescribed Burn) ---
        longterm_frame = tk.Frame(self)
        longterm_frame.pack(fill=tk.BOTH)

        tk.Label(longterm_frame, text="Long-Term Prevention",
                 font=("TkDefaultFont", 9, "bold")).pack(anchor=tk.W, pady=(0, 4))

        grazing_row = tk.Frame(longterm_frame)
        grazing_row.pack(fill=tk.BOTH, pady=2)

        self.animals_var = tk.StringVar(
            value=os.environ.get("CA_GRAZING_ANIMALS", "0")
        )
        os.environ["CA_GRAZING_ANIMALS"] = self.animals_var.get()

        animals_menu = tk.OptionMenu(
            grazing_row,
            self.animals_var,
            "0", "5000", "10000", "25000", "50000",
            command=lambda val: os.environ.__setitem__("CA_GRAZING_ANIMALS", val)
        )
        animals_menu.pack(side=tk.RIGHT)
        tk.Label(grazing_row, text="Grazing Animals:").pack(side=tk.RIGHT)

        forest_row = tk.Frame(longterm_frame)
        forest_row.pack(fill=tk.BOTH, pady=2)
        
        self.forest_var = tk.StringVar(
                    value=os.environ.get("CA_FOREST_EXTENSION", "NONE")
                )
        os.environ["CA_FOREST_EXTENSION"] = self.forest_var.get()
        
        forest_menu = tk.OptionMenu(
            forest_row,
            self.forest_var,
            "0", "1", "2",
            command=lambda val: os.environ.__setitem__("CA_FOREST_EXTENSION", val)
        )
        forest_menu.pack(side=tk.RIGHT)
        tk.Label(forest_row, text="Forest Extension:").pack(side=tk.RIGHT)

        preburn_row = tk.Frame(longterm_frame)
        preburn_row.pack(fill=tk.BOTH, pady=2)

        self.preburn_var = tk.StringVar(
            value=os.environ.get("CA_PREBURN_STRATEGY", "NONE")
        )
        os.environ["CA_PREBURN_STRATEGY"] = self.preburn_var.get()

        preburn_menu = tk.OptionMenu(
            preburn_row,
            self.preburn_var,
            "NONE", "TOWN_PERIMETER", "CORRIDOR_STRIP", "FULL_NETWORK",
            command=lambda val: os.environ.__setitem__("CA_PREBURN_STRATEGY", val)
        )
        preburn_menu.pack(side=tk.RIGHT)
        tk.Label(preburn_row, text="Prescribed Burn:").pack(side=tk.RIGHT)

        marsh_row = tk.Frame(longterm_frame)
        marsh_row.pack(fill=tk.BOTH, pady=2)

        self.marsh_var = tk.BooleanVar(
            value=os.environ.get("CA_MARSH_ENABLED", "1") == "1"
        )
        os.environ["CA_MARSH_ENABLED"] = "1" if self.marsh_var.get() else "0"

        marsh_check = tk.Checkbutton(
            marsh_row,
            variable=self.marsh_var,
            command=lambda: os.environ.__setitem__(
                "CA_MARSH_ENABLED", "0" if self.marsh_var.get() else "1"
            )
        )
        marsh_check.pack(side=tk.RIGHT)
        tk.Label(marsh_row, text="Marshland").pack(side=tk.RIGHT)

        self.separator()

        #Active Suppression (Water Drop)
        water_group = tk.Frame(self)
        water_group.pack(fill=tk.BOTH)

        tk.Label(water_group, text="Active Suppression (12.5 km² Water)",
                 font=("TkDefaultFont", 9, "bold")).pack(anchor=tk.W, pady=(0, 4))

        water_row = tk.Frame(water_group)
        water_row.pack(fill=tk.BOTH, pady=2)

        self.water_var = tk.StringVar(
            value=os.environ.get("CA_WATER_STRATEGY", "TOWN_SURROUND")
        )
        os.environ["CA_WATER_STRATEGY"] = self.water_var.get()

        water_menu = tk.OptionMenu(
            water_row,
            self.water_var,
            "NONE", "TOWN_SURROUND", "SINGLE_BLOCK", "TWO_LINES", "ACTIVE_FRONT",
            command=lambda val: os.environ.__setitem__("CA_WATER_STRATEGY", val)
        )
        water_menu.pack(side=tk.RIGHT)
        tk.Label(water_row, text="Water Strategy:").pack(side=tk.RIGHT)

        #Grid dimensions (fixed at 100x100 in main.py) ---
        # if self.ca_config.dimensions == 2:
        #     self.griddims_entry = _GridDimensionsUI(self)
        #     self.griddims_entry.pack(fill=tk.BOTH)
        # else:
        #     self.rulenum_entry = _RuleNumberUI(self)
        #     self.rulenum_entry.pack(fill=tk.BOTH)

        self.separator()

        # Generations
        self.generations_entry = _GenerationsUI(self)
        self.generations_entry.pack(fill=tk.BOTH)

        #Neighbourhood selector
        # self.separator()
        # self.nhood_select = _NeighbourhoodUI(self, self.ca_config.dimensions)
        # self.nhood_select.pack(fill=tk.BOTH)

        # --- Commented out: Initial grid options (fixed map in main.py) ---
        # self.separator()
        # self.init_grid = _InitialGridUI(self, self.ca_config)
        # self.init_grid.pack(fill=tk.BOTH)

        self.separator()

        # Colour selector
        self.state_colors = _StateColorsUI(self, self.ca_config, self.ca_graph)
        self.state_colors.pack(fill=tk.BOTH)

        self.separator()

        # refresh the frame and graph
        self.update(self.ca_config, self.ca_graph)

    def separator(self):
        """Generate a separator"""
        return _Separator(self).pack(fill=tk.BOTH, padx=5, pady=8)

    def reset(self):
        """Reset all options to software defaults"""
        # if self.ca_config.dimensions == 2:
        #     self.griddims_entry.set_default()
        # else:
        #     self.rulenum_entry.set_default()
        self.generations_entry.set_default()
        # self.nhood_select.set_default()
        self.wind_var.set("SE")
        os.environ["CA_WIND"] = "SE"
        self.animals_var.set("0")
        os.environ["CA_GRAZING_ANIMALS"] = "0"
        self.water_var.set("TOWN_SURROUND")
        os.environ["CA_WATER_STRATEGY"] = "TOWN_SURROUND"
        self.preburn_var.set("NONE")
        os.environ["CA_PREBURN_STRATEGY"] = "NONE"
        self.marsh_var.set(True)
        os.environ["CA_MARSH_ENABLED"] = "0"
        self.burn_var.set("Power Plant")
        os.environ["CA_BURN_LOCATION"] = "Power Plant"

    def get_config(self, ca_config, validate=False):
        """Get the config from the UI and store in a CAConfig object"""
        ca_config.num_generations = self.generations_entry.get_value()
        ca_config.state_colors = self.state_colors.get_value()

        # if ca_config.dimensions == 2:
        #     ca_config.grid_dims = self.griddims_entry.get_value()
        #     ca_config.nhood_arr = self.nhood_select.get_value() + 0
        # else:
        #     ca_config.rule_num = self.rulenum_entry.get_value()
        #     ca_config.nhood_arr = self.nhood_select.get_value()[0] + 0
        #     centercell = (self.init_grid.selected.get() == 2)
        #     if centercell:
        #         ca_config.grid_dims = gens_to_dims(ca_config.num_generations)
        #         ca_config.initial_grid = np.zeros(ca_config.grid_dims)
        #         ig = self.__center_cell_set(ca_config.grid_dims,
        #                                     ca_config.states[-1])
        #         ca_config.set_initial_grid(ig)

        if not validate:
            return ca_config
        else:
            return self.__validate_and_warn(ca_config)

    def __center_cell_set(self, dims, state):
        new_row = np.zeros((1, dims[1]))
        center = dims[1]//2
        new_row[0, center] = state
        return new_row

    def __validate_and_warn(self, ca_config):
        """Validate the CAConfig object against criteria"""
        errcheck = self.__error_cases(ca_config)
        if errcheck is not None:
            alerterror(*errcheck)
            return ca_config, False

        # If complex task ask if user wishes to proceed
        proceedcheck = self.__ask_proceed_cases(ca_config)
        return ca_config, proceedcheck

    def __error_cases(self, ca_config):
        if ca_config.dimensions == 1:
            if ca_config.rule_num < 0 or ca_config.rule_num > 255:
                s = "Only 0-255 valid, {val} supplied"
                return "Rule number", s.format(val=ca_config.rule_num)

        if ca_config.dimensions == 2:
            if ca_config.grid_dims[0] < 3 or ca_config.grid_dims[1] < 3:
                s = "One or both of the grid dimensions is too small {d}"
                return ("Grid dimensions", s.format(d=ca_config.grid_dims))

        if ca_config.num_generations < 1:
            s = "Invalid generations {val} supplied"
            return "Generations", s.format(val=ca_config.num_generations)
        return None

    def __ask_proceed_cases(self, ca_config):
        complexity_val = (ca_config.num_generations * ca_config.grid_dims[0] *
                          ca_config.grid_dims[1])
        if complexity_val > 30000000:
            s = ("The combination of grid dims {d} and {x} generations may" +
                 " take a long time to run. Do you wish to continue?")
            s = s.format(d=ca_config.grid_dims, x=ca_config.num_generations)
            complexitycheck = alertcontinue("Complexity warning!", s)
            return complexitycheck
        return True

    def update(self, ca_config, ca_graph):
        self.ca_config = ca_config
        self.ca_graph = ca_graph
        # if ca_config.dimensions == 2:
        #     self.griddims_entry.set(self.griddims_entry.COLS,
        #                             self.ca_config.grid_dims[0])
        #     self.griddims_entry.set(self.griddims_entry.ROWS,
        #                             self.ca_config.grid_dims[1])
        # else:
        #     self.rulenum_entry.set(ca_config.rule_num)
        # self.nhood_select.set(self.ca_config.nhood_arr)
        self.generations_entry.set(self.ca_config.num_generations)
        # self.init_grid.update_config(self.ca_config)
        self.state_colors.update(self.ca_config, ca_graph)