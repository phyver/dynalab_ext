#!/usr/bin/env python
# coding=utf-8

import inkex
import fablab
import random


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
                bb = elem.bounding_box(transform=True)
                r = random.randrange(0, 6)
                if r == 0:
                    self.new_error_arrow(bb.left, bb.top, msg="lorem")
                elif r == 1:
                    self.new_warning_arrow(bb.left, bb.top, msg="lorem")
                elif r == 2:
                    self.new_note_arrow(bb.left, bb.top, msg="lorem")
                elif r == 3:
                    self.outline_bounding_box(elem, color="#f00", msg="lorem")
                elif r == 4:
                    self.outline_bounding_box(elem, color=inkex.Color("orange"), msg="lorem")
                elif r == 5:
                    self.outline_bounding_box(elem, color="#0f0", msg="lorem")

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
