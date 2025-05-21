#!/usr/bin/env python
# coding=utf-8

import inkex
import fablab


class Init(fablab.FablabExtension):

    def add_arguments(self, pars):
        pass    # We don't need arguments for this extension

    def effect(self):
        # make sure the unit is "mm"
        self.svg.namedview.set(inkex.addNS('document-units', 'inkscape'), 'mm')

        self.init_error_layer()


if __name__ == '__main__':
    Init().run()
