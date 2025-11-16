#!/usr/bin/env python

from lib import config, dynalab


class LoadConfig(dynalab.Ext):
    """
    load an existing config file (json) and use it as the new default
    configuration
    """

    def add_arguments(self, pars):
        pass

    def effect(self):
        self.load_config(config.DEFAULT_CONFIG_FILE)
        self.show_config()


if __name__ == "__main__":
    LoadConfig().run()
