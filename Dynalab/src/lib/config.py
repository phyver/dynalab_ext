#!/usr/bin/env python
# coding=utf-8

import json
import os

from gettext import gettext as _

import inkex

DEFAULT_CONFIG_FILE = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "default_config.json"))
CURRENT_CONFIG_FILE = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "current_config.json"))

DEFAULT_CONFIG = {
    "verbosity": 1,
    "artefacts_locked": False,
    "artefacts_grouped": True,
    "artefacts_stroke_width": 1,
    #
    "laser_diameter": 0.2,
    "laser_mode_cut_color": "#ff0000",
    "laser_mode_fill_color": "#0000ff",
    "laser_mode_line_color": "#000000",
    #
    "size_tiny_element": 0.5,
}


class Ext():

    config = None

    def __init__(self):
        super().__init__()
        self.load_config()

    def reset_config(self):
        self.load_config(DEFAULT_CONFIG_FILE)

    def load_config(self, filename=CURRENT_CONFIG_FILE):
        try:
            f = open(filename, mode="rt")
            self.config = json.load(f)
            f.close()

        except FileNotFoundError as err:
            if os.path.realpath(filename) == DEFAULT_CONFIG_FILE or os.path.realpath(filename) == CURRENT_CONFIG_FILE:
                self.config = DEFAULT_CONFIG.copy()
            else:
                msg = _("FILE NOT FOUND:")
                raise inkex.AbortExtension(f"\n{msg} {filename}\n{err}")
        except (IOError, OSError) as err:
            msg = _("ERROR READING FILE:")
            raise inkex.AbortExtension(f"\n{msg} {filename}\n{err}")
        except json.JSONDecodeError as err:
            msg = _("INVALID CONFIG FILE:")
            raise inkex.AbortExtension(f"\n{msg} {filename}\n{err}")

        for k, v in DEFAULT_CONFIG.items():
            if k not in self.config:
                self.config[k] = v

        for k in list(self.config.keys()):
            if k not in DEFAULT_CONFIG:
                del self.config[k]

        # save config so that future run use this new configuration
        self.save_config(CURRENT_CONFIG_FILE)

    def save_config(self, filename, **kwargs):
        filename = os.path.realpath(filename)
        if filename == DEFAULT_CONFIG_FILE:
            raise inkex.AbortExtension(f"CANNOT OVERWRITE DEFAULT CONFIG FILE {filename}")

        try:
            with open(filename, mode="wt") as f:
                for k, v in kwargs:
                    self.config[k] = v
                    # TODO: should I validate that keys and values are valid???

                f.write(json.dumps(self.config, indent=2, sort_keys=True))
        except (FileNotFoundError, PermissionError, IsADirectoryError, OSError) as err:
            raise inkex.AbortExtension(f"CANNOT SAVE CONFIG TO {filename}: {err}")

    def show_config(self):
        self.msg("""
  - laser diameter: {laser_diameter:.2f}mm
  - laser cut mode color: {laser_mode_cut_color:s}
  - laser fill mode color: {laser_mode_fill_color:s}
  - laser line mode color: {laser_mode_line_color:s}

  - size for "tiny" elements: {size_tiny_element}mm

  - artefacts layer is locked (non selectable): {artefacts_locked}
  - artefacts are put in a single group: {artefacts_grouped}
  - stroke width for artefacts: {artefacts_stroke_width}mm
  - verbosity level: {verbosity}
""".format(**self.config))
