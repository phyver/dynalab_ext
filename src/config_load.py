#!/usr/bin/env python

from lib import config
import os


class LoadConfig(config.ConfigExt):

    def add_arguments(self, pars):
        default_path = os.path.dirname(os.path.realpath(__file__))
        pars.add_argument("--config-file", default=default_path, help="Load file", dest="config_file")

    def effect(self):
        self.load_config(self.options.config_file)
        self.show_config()


if __name__ == '__main__':
    LoadConfig().run()
