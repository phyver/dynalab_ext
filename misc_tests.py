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

        self.init_error_layer()

        # mark the selected elements
        for elem, tr in self.svg.selection or self.all_elements(recurse=True, skip_groups=True, limit=5):
            r = random.randrange(0, 6)
            if r == 0:
                self.new_error_arrow(elem, tr, msg="lorem")
            elif r == 1:
                self.new_warning_arrow(elem, tr, msg="lorem")
            elif r == 2:
                self.new_note_arrow(elem, tr, msg="lorem")
            elif r == 3:
                self.outline_bounding_box(elem, tr, color="#f00", msg="lorem")
            elif r == 4:
                self.outline_bounding_box(elem, tr, color=inkex.Color("orange"), msg="lorem")
            elif r == 5:
                self.outline_bounding_box(elem, tr, color="#0f0", msg="lorem")



if __name__ == '__main__':
    MiscTests().run()
