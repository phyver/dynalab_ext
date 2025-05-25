#!/usr/bin/env python

from lib import fablab


class Init(fablab.Ext):
    """
    initialize the error layer
    """

    def add_arguments(self, pars):
        pass

    def effect(self):
        self.init_artefact_layer()


if __name__ == '__main__':
    Init().run()
