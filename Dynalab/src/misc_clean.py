#!/usr/bin/env python

from lib import dynalab


class Clean(dynalab.Ext):
    """
    remove the error layer
    """

    def add_arguments(self, pars):
        pass

    def effect(self):
        self.extract_non_artifacts()
        self.clean_artifacts(force=True)


if __name__ == "__main__":
    Clean().run()
