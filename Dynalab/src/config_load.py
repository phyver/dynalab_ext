#!/usr/bin/env python

import os

from lib import dynalab


class LoadConfig(dynalab.Ext):
    """
    load an existing config file (json) and use it as the new default
    configuration
    """

    def add_arguments(self, pars):
        default_path = os.path.dirname(os.path.realpath(__file__))
        pars.add_argument("--config-file", default=default_path, dest="config_file", help="Load file")

    def effect(self):
        self.load_config(self.options.config_file)
        self.show_config()


if __name__ == "__main__":
    LoadConfig().run()
