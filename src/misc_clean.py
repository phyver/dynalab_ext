#!/usr/bin/env python

from lib import fablab


class Clean(fablab.Ext):

    def add_arguments(self, pars):
        pass    # We don't need arguments for this extension

    def effect(self):
        self.clean(force=True)


if __name__ == '__main__':
    Clean().run()
