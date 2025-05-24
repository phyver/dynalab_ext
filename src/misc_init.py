#!/usr/bin/env python

from lib import fablab


class Init(fablab.Ext):

    def add_arguments(self, pars):
        pass    # We don't need arguments for this extension

    def effect(self):
        self.init()
        self.init_error_layer()


if __name__ == '__main__':
    Init().run()
