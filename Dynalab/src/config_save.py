#!/usr/bin/env python

from gettext import gettext as _

import inkex

from lib import dynalab, config


class SaveConfig(dynalab.Ext):
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

        pars.add_argument("--lock-artefacts", type=inkex.Boolean, dest="artefacts_locked",
                          help=_("lock artefacts layer"))
        pars.add_argument("--group-artefacts", type=inkex.Boolean, dest="artefacts_grouped",
                          help=_("group artefacts"))
        pars.add_argument("--artefacts-stroke-width", type=float, dest="artefacts_stroke_width",
                          help=_("stroke width for artefacts (mm)"))
        pars.add_argument("--verbosity", type=int, help=_("verbosity"))

        pars.add_argument("--save-file", dest="save_file", help=_("Save file"))

    def effect(self):

        options = vars(self.options)
        for k in config.DEFAULT_CONFIG:
            if options[k] is not None:
                self.config[k] = options[k]

        if self.options.save_file:
            self.save_config(self.options.save_file)
            self.msg(f"""
### The following configuration was saved to {self.options.save_file}
                     """)

        self.save_config(config.CURRENT_CONFIG_FILE)
        self.show_config()


if __name__ == "__main__":
    SaveConfig().run()
