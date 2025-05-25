#!/usr/bin/env python
# coding=utf-8

import json
import os

from gettext import gettext as _

import inkex

DEFAULT_CONFIG_FILE = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "current_config.json"))

DEFAULT_CONFIG = {
    "misc_laser_diameter": 0.1,
    "laser_mode_cut_color": "#ff0000",
    "laser_mode_fill_color": "#0000ff",
    "laser_mode_line_color": "#000000",
    "size_tiny_element": 0.5,
}


class Ext():

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

        except FileNotFoundError as err:
            if os.path.realpath(filename) == DEFAULT_CONFIG_FILE:
                self.config = DEFAULT_CONFIG.copy()
            else:
                msg = _("FILE NOT FOUND:")
                raise inkex.AbortExtension(f"\n\n{msg} {filename}\n{err}\n\n")
        except (IOError, OSError) as err:
            msg = _("ERROR READING FILE:")
            raise inkex.AbortExtension(f"\n\n{msg} {filename}\n{err}\n\n")
        except json.JSONDecodeError as err:
            msg = _("INVALID CONFIG FILE:")
            raise inkex.AbortExtension(f"\n\n{msg} {filename}\n{err}\n\n")

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


laser diameter: {misc_laser_diameter:.2f}mm

cut color: \t{laser_mode_cut_color:s}
fill color: \t{laser_mode_fill_color:s}
line color: \t{laser_mode_line_color:s}

size under which an element is tagged "tiny": {size_tiny_element}


""".format(**self.config))
