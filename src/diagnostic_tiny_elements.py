#!/usr/bin/env python
# coding=utf-8

import inkex
from inkex import units
from lib import fablab


class MiscTests(fablab.FablabExtension):

    def add_arguments(self, pars):
        pass    # We don't need arguments for this extension

    def effect(self):
        self.init()
        self.init_error_layer()

        # mark the selected elements
        for elem, tr in self.selected_or_all(recurse=True,
                                             skip_groups=True,
                                             limit=None):
            if isinstance(elem, inkex.TextElement):
                # TODO???
                continue
            bb = elem.shape_box()
            if units.convert_unit(bb.width, "mm") < 2 and units.convert_unit(bb.height, "mm") < 2:
                self.new_error_arrow(elem, tr, msg="tiny element")
                self.outline_bounding_box(elem, tr, color="#f00", msg="tiny element")

        self.clean(force=False)


if __name__ == '__main__':
    MiscTests().run()
