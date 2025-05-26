#!/usr/bin/env python

import os
from gettext import gettext as _

import inkex

from lib import artefacts, config


class SaveConfig(artefacts.Ext):
    """
    save a new configuration file in a user chosen location
    All configuration options that aren"t given are taken from the current
    configuration file.
    Note that due to the way extensions are run, it is not possible to display
    the current values inside the form (inx file).
    """

    def add_arguments(self, pars):
        pars.add_argument("--tabs")      # to ignore the dummy parameter used for tabs

        pars.add_argument("--laser-diameter", type=float, dest="laser_diameter",
                          help=_("laser diameter (mm)"))

        pars.add_argument("--cut-color", type=str, dest="laser_mode_cut_color",
                          help=_("cutting color (#RGB)"))
        pars.add_argument("--fill-color", type=str, dest="laser_mode_fill_color",
                          help=_("fill engraving color (#RGB)"))
        pars.add_argument("--line-color", type=str, dest="laser_mode_line_color",
                          help=_("line engraving color (#RGB)"))

        pars.add_argument("--size-tiny-element", type=float, dest="size_tiny_element",
                          help=_("size for tiny elements (mm)"))

        pars.add_argument("--lock-artefacts", type=inkex.Boolean, dest="lock_artefacts",
                          help=_("lock artefacts layer"))
        pars.add_argument("--group-artefacts", type=inkex.Boolean, dest="group_artefacts",
                          help=_("group artefacts"))
        pars.add_argument("--artefacts-stroke-width", type=float, dest="artefacts_stroke_width",
                          help=_("stroke width for artefacts (mm)"))

        pars.add_argument("--config-dir", dest="config_dir",
                          help=_("Save directory"))
        pars.add_argument("--config-file", dest="config_file",
                          help=_("config filename"))

    def effect(self):

        options = vars(self.options)
        for k in config.DEFAULT_CONFIG:
            if options[k] is not None:
                self.config[k] = options[k]

        if self.options.config_dir and self.options.config_file:
            filename = os.path.join(self.options.config_dir, self.options.config_file)
            self.save_config(filename)
            self.msg(f"""
The following configuration was saved to {filename}
                     """)

        self.save_config(config.DEFAULT_CONFIG_FILE)
        self.show_config()


if __name__ == "__main__":
    SaveConfig().run()
