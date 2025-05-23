#!/usr/bin/env python
# coding=utf-8

import inkex
import json
import os

CONFIG_FILE = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "current_config.json"))


class SaveConfig(inkex.EffectExtension):

    def add_arguments(self, pars):
        default_path = os.path.dirname(os.path.realpath(__file__))
        pars.add_argument('--laser-diameter', type=float, default=0.1, help='diametre du laser (mm)', dest="laser_diameter")

        pars.add_argument('--cut-color', type=str, default="#ff0000", help='cutting color (#RGB)', dest="cut_color")
        pars.add_argument('--fill-color', type=str, default="#0000ff", help='fill engraving color (#RGB)', dest="fill_color")
        pars.add_argument('--line-color', type=str, default="#000000", help='line engraving color (#RGB)', dest="line_color")

        pars.add_argument("--config-dir", default=default_path, help="Save directory", dest="config_dir")
        pars.add_argument("--config-file", help="config filename", dest="config_file")

    def effect(self):

        # TODO: if self.options.config_file is equal to CONFIG_FILE, abort
        config_file = os.path.realpath(os.path.join(self.options.config_dir, self.options.config_file))
        if config_file == CONFIG_FILE:
            raise inkex.AbortExtension("Don't save configuration to the default configuration file: it is overwritten")

        f = open(self.options.config_file, mode="wt")
        # TODO deal with exceptions

        config = {}
        # TODO load current values, and use them as default values (they won't appear in the widges)

        config["laser_diameter"] = self.options.laser_diameter
        f.write(json.dumps(config))
        f.close()
        self.msg("SHOW VALUES")


if __name__ == '__main__':
    SaveConfig().run()
