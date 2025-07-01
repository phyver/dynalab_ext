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

        pars.add_argument("--lock-artifacts", type=inkex.Boolean, dest="artifacts_locked",
                          help=_("lock artifacts layer"))
        pars.add_argument("--group-artifacts", type=inkex.Boolean, dest="artifacts_grouped",
                          help=_("group artifacts"))
        pars.add_argument("--artifacts-opacity", type=int, default=75,
                          dest="artifacts_opacity",
                          help=_("artifacts opacity (%)"))
        pars.add_argument("--artifacts-overlay-opacity", type=int, default=5,
                          dest="artifacts_overlay_opacity",
                          help=_("artifacts overlay opacity (%)"))
        pars.add_argument("--artifacts-stroke-width", type=float, dest="artifacts_stroke_width",
                          help=_("stroke width for artifacts (mm)"))
        pars.add_argument("--verbosity", type=int, help=_("verbosity"))

        pars.add_argument("--save-file", dest="save_file", help=_("Save file"))

    def effect(self):

        changed = []
        options = vars(self.options)
        for k in config.DEFAULT_CONFIG:
            if options[k] is not None and options[k] != "":
                if options[k] != self.config[k]:
                    self.config[k] = options[k]
                    changed.append(k)

        if len(changed) == 0:
            self.message("No configuration option has been changed!")
        else:
            self.save_config(config.CURRENT_CONFIG_FILE)
            self.message("The following configuration options have been changed:")
            self.show_config(changed)

        if self.options.save_file:
            self.save_config(self.options.save_file)
            self.message("")
            self.message(f"The configuration was saved to {self.options.save_file}")


if __name__ == "__main__":
    SaveConfig().run()
