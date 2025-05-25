#!/usr/bin/env python

from gettext import gettext as _

import inkex
from inkex import units

from lib import fablab


class MarkTiny(fablab.Ext):
    """
    tags the "tiny" elements found in the document
    """

    def add_arguments(self, pars):
        pars.add_argument("--size-tiny-element", type=float, dest="size_tiny_element",
                          help=_("size for tiny elements (mm)"))

    def effect(self, clean=True):
        self.init_artefact_layer()
        tiny = self.options.size_tiny_element or self.config["size_tiny_element"]

        # mark the selected elements
        for elem, tr in self.selected_or_all(recurse=True,
                                             skip_groups=True,
                                             limit=None):
            if isinstance(elem, inkex.TextElement):
                # TODO do something???
                continue
            bb = elem.shape_box()
            if units.convert_unit(bb.width, "mm") < tiny and units.convert_unit(bb.height, "mm") < tiny:
                desc = f"{_('tiny element')} (id: {elem.get_id()})"
                self.new_error_arrow(elem, tr, msg=desc)
                self.outline_bounding_box(elem, tr, color="#f00", msg=desc)

        if clean:
            self.clean(force=False)


if __name__ == '__main__':
    MarkTiny().run()
