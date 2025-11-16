#!/usr/bin/env python

from lib import dynalab


class ShowConfig(dynalab.Ext):
    """
    display the current configuration options
    """

    def add_arguments(self, pars):
        pass

    def effect(self):
        self.show_config()


if __name__ == "__main__":
    ShowConfig().run()
