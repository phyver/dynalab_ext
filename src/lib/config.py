#!/usr/bin/env python
# coding=utf-8

import inkex
import json
import os

DEFAULT_CONFIG_FILE = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "current_config.json"))

DEFAULT_CONFIG = {
    "misc_laser_diameter": 0.1,
    "laser_mode_cut_color": "#ff0000",
    "laser_mode_fill_color": "#0000ff",
    "laser_mode_line_color": "#000000",
}


class Ext(inkex.EffectExtension):

    config = None

    def __init__(self):
        super().__init__()
        self.load_config()

    def load_config(self, filename=DEFAULT_CONFIG_FILE):
        try:
            with open(filename, mode="rt") as f:
                self.config = json.load(f)

                for k, v in DEFAULT_CONFIG.items():
                    if k not in self.config:
                        self.config[k] = v

                for k in list(self.config.keys()):
                    if k not in DEFAULT_CONFIG:
                        del self.config[k]

            self.save_config(DEFAULT_CONFIG_FILE)

        except FileNotFoundError:
            if os.path.realpath(filename) == DEFAULT_CONFIG_FILE:
                self.config = DEFAULT_CONFIG.copy()
            else:
                raise inkex.AbortExtension(f"FILE NOT FOUND: {filename}")
        except (IOError, OSError):
            raise inkex.AbortExtension(f"ERROR READING FILE: {filename}")
        except json.JSONDecodeError:
            raise inkex.AbortExtension(f"INVALID CONFIG FILE: {filename}")

    def save_config(self, filename, **kwargs):
        filename = os.path.realpath(filename)

        try:
            with open(filename, mode="wt") as f:
                for k, v in kwargs:
                    self.config[k] = v
                    # TODO: check keys and values are valid???

                f.write(json.dumps(self.config, indent=2, sort_keys=True))
        except (FileNotFoundError, PermissionError, IsADirectoryError, OSError) as err:
            raise inkex.AbortExtension(f"CANNOT SAVE CONFIG TO {filename}: {err}")

    def show_config(self):
        self.msg("""


laser diameter: {misc_laser_diameter:f}mm

cut color: \t{laser_mode_cut_color:s}
fill color: \t{laser_mode_fill_color:s}
line color: \t{laser_mode_line_color:s}


""".format(**self.config))
