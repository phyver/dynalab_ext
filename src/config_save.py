#!/usr/bin/env python

from lib import config
import os


class SaveConfig(config.ConfigExt):

    def add_arguments(self, pars):
        pars.add_argument('--laser-diameter', type=float, help='diametre du laser (mm)', dest="misc_laser_diameter")

        pars.add_argument('--cut-color', type=str, help='cutting color (#RGB)', dest="laser_mode_cut_color")
        pars.add_argument('--fill-color', type=str, help='fill engraving color (#RGB)', dest="laser_mode_fill_color")
        pars.add_argument('--line-color', type=str, help='line engraving color (#RGB)', dest="laser_mode_line_color")

        pars.add_argument("--config-dir", help="Save directory", dest="config_dir")
        pars.add_argument("--config-file", help="config filename", dest="config_file")

    def effect(self):

        options = vars(self.options)
        for k in config.DEFAULT_CONFIG:
            if options[k]:
                self.config[k] = options[k]

        filename = os.path.join(self.options.config_dir, self.options.config_file)
        self.save_config(filename)
        self.load_config(filename)
        self.show_config()


if __name__ == '__main__':
    SaveConfig().run()
