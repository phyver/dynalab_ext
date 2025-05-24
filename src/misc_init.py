#!/usr/bin/env python
# coding=utf-8

from lib import fablab


class Init(fablab.FablabExtension):

    def add_arguments(self, pars):
        pass    # We don't need arguments for this extension

    def effect(self):
        self.init()
        self.init_error_layer()


if __name__ == '__main__':
    Init().run()
