#!/usr/bin/env python

from lib import artefacts


class Clean(artefacts.Ext):
    """
    remove the error layer
    """

    def add_arguments(self, pars):
        pass

    def effect(self):
        self.extract_non_artefacts()
        self.clean(force=True)


if __name__ == '__main__':
    Clean().run()
