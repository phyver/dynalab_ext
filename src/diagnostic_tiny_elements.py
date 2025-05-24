#!/usr/bin/env python

from gettext import gettext as _

import inkex
from inkex import units

from lib import fablab


class DetectTiny(fablab.Ext):
    """
    tags the "tiny" elements found in the document
    """

    def add_arguments(self, pars):
        pass

    def effect(self):
        self.init_error_layer()

        # mark the selected elements
        for elem, tr in self.selected_or_all(recurse=True,
                                             skip_groups=True,
                                             limit=None):
            if isinstance(elem, inkex.TextElement):
                # TODO do something???
                continue
            bb = elem.shape_box()
            if units.convert_unit(bb.width, "mm") < 2 and units.convert_unit(bb.height, "mm") < 2:
                desc = f"{_('tiny element')} (id: {elem.get_id()})"
                self.new_error_arrow(elem, tr, msg=desc)
                self.outline_bounding_box(elem, tr, color="#f00", msg=desc)

        self.clean(force=False)


if __name__ == '__main__':
    DetectTiny().run()
