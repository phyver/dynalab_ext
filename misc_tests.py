#!/usr/bin/env python
# coding=utf-8

import inkex
import fablab


class MiscTests(fablab.FablabExtension):

    def add_arguments(self, pars):
        pass    # We don't need arguments for this extension

    def effect(self):
        # make sure the unit is "mm"
        self.svg.namedview.set(inkex.addNS('document-units', 'inkscape'), 'mm')

        self.init_error()

        # mark the selected elements
        for elem in self.svg.selection or self.all_objects():
            try:
                bb = elem.bounding_box()
                self.new_error(bb.left, bb.top, "lorem")
            except AttributeError:
                # error elements (in the error layer) that could have been
                # selected have been cleared by the init_error method
                # they don't have a bounding box (elem.bounding_box() returns
                # None, so that bb.left / bb.top raises the AttributeError
                # exception)
                # and we shouldn't tag error objects anyway!
                continue


if __name__ == '__main__':
    MiscTests().run()
