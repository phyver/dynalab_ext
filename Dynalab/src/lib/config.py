#!/usr/bin/env python
# coding=utf-8

import json
import os
from collections import OrderedDict
from gettext import gettext as _

import inkex

DEFAULT_CONFIG_FILE = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "default_config.json"))
CURRENT_CONFIG_FILE = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "current_config.json"))

DEFAULT_CONFIG = OrderedDict(
    {
        "verbosity": (1, _("verbosity level: {verbosity}")),
        "artifacts_locked": (False, _("artifacts layer is locked (non selectable): {artifacts_locked}")),
        "artifacts_grouped": (True, _("artifacts are put in a single group: {artifacts_grouped}")),
        "artifacts_stroke_width": (1, _("stroke width for artifacts: {artifacts_stroke_width}mm")),
        "artifacts_opacity": (75, _("artifacts opacity: {artifacts_opacity}%")),
        "artifacts_overlay_opacity": (5, _("artifacts overlay stripes opacity: {artifacts_overlay_opacity}%")),
        #
        "laser_diameter": (0.2, _("laser diameter: {laser_diameter:.2f}mm")),
        "laser_mode_cut_color": ("#ff0000", _("laser cut mode color: {laser_mode_cut_color:s}")),
        "laser_mode_fill_color": ("#0000ff", _("laser fill mode color: {laser_mode_fill_color:s}")),
        "laser_mode_line_color": ("#000000", _("laser line mode color: {laser_mode_line_color:s}")),
        #
        "size_tiny_element": (0.5, _("size for 'tiny' elements: {size_tiny_element}mm")),
    }
)


class Ext:

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
                self.config = {o: v[0] for o, v in DEFAULT_CONFIG.items()}
            else:
                raise inkex.AbortExtension(
                    """
{}
  => {}
""".format(
                        _("FILE NOT FOUND: {filename:s}").format(filename=filename), err
                    )
                )

        except (IOError, OSError) as err:
            raise inkex.AbortExtension(
                """
{}
  => {}
""".format(
                    _("ERROR READING FILE: {filename:s}").format(filename=filename), err
                )
            )

        except json.JSONDecodeError as err:
            raise inkex.AbortExtension(
                """
{}
  => {}
""".format(
                    _("INVALID CONFIG FILE: {filename:s}").format(filename=filename), err
                )
            )

        for k, v in DEFAULT_CONFIG.items():
            if k not in self.config:
                self.config[k] = v[0]

        for k in list(self.config.keys()):
            if k not in DEFAULT_CONFIG:
                del self.config[k]

        # save config so that future run use this new configuration
        self.save_config(CURRENT_CONFIG_FILE)

    def save_config(self, filename, **kwargs):
        filename = os.path.realpath(filename)
        if filename == DEFAULT_CONFIG_FILE:
            raise inkex.AbortExtension(_("CANNOT OVERWRITE DEFAULT CONFIG FILE: {filename}").format(filename=filename))

        try:
            with open(filename, mode="wt") as f:
                for k, v in kwargs:
                    self.config[k] = v
                    # TODO: should I validate that keys and values are valid???
                    # colors => ^$|^#[0-9a-fA-F]{6}$|^#[0-9a-fA-F]{3}$

                f.write(json.dumps(self.config, indent=2, sort_keys=True))
        except (FileNotFoundError, PermissionError, IsADirectoryError, OSError) as err:
            raise inkex.AbortExtension(f"CANNOT SAVE CONFIG TO {filename}: {err}")
            raise inkex.AbortExtension(
                """
{}
  => {}
""".format(
                    _("CANNOT SAVE CONFIG TO {filename:s}").format(filename=filename), err
                )
            )

    def show_config(self, args=None):
        if args is None:
            args = DEFAULT_CONFIG.keys()
        for arg in args:
            self.msg("  - " + DEFAULT_CONFIG[arg][1].format(**self.config))
