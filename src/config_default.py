#!/usr/bin/env python

from lib import artefacts, config


class LoadConfig(artefacts.Ext):
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
