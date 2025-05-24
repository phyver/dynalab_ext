#!/usr/bin/env python
# coding=utf-8

import fablab


class Clean(fablab.FablabExtension):

    def add_arguments(self, pars):
        pass    # We don't need arguments for this extension

    def effect(self):
        self.clean()


if __name__ == '__main__':
    Clean().run()
