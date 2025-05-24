#!/usr/bin/env python

import os
from gettext import gettext as _

from lib import config, i18n


class SaveConfig(config.Ext, i18n.Ext):
    """
    save a new configuration file in a user chosen location
    All configuration options that aren"t given are taken from the current
    configuration file.
    Note that due to the way extensions are run, it is not possible to display
    the current values inside the form (inx file).
    """

    def add_arguments(self, pars):
        pars.add_argument("--laser-diameter", type=float, dest="misc_laser_diameter",
                          help=_("laser diameter (mm)"))

        pars.add_argument("--cut-color", type=str, dest="laser_mode_cut_color",
                          help=_("cutting color (#RGB)"))
        pars.add_argument("--fill-color", type=str, dest="laser_mode_fill_color",
                          help=_("fill engraving color (#RGB)"))
        pars.add_argument("--line-color", type=str, dest="laser_mode_line_color",
                          help=_("line engraving color (#RGB)"))

        pars.add_argument("--config-dir", dest="config_dir",
                          help=_("Save directory"))
        pars.add_argument("--config-file", dest="config_file",
                          help=_("config filename"))

    def effect(self):

        options = vars(self.options)
        for k in config.DEFAULT_CONFIG:
            if options[k]:
                self.config[k] = options[k]

        filename = os.path.join(self.options.config_dir, self.options.config_file)
        self.save_config(filename)
        self.load_config(filename)
        self.show_config()


if __name__ == "__main__":
    SaveConfig().run()
