#!/usr/bin/env python

from gettext import gettext as _, ngettext

import inkex

from lib import dynalab
from lib.dynalab import WARNING


class MarkOutside(dynalab.Ext):
    """
    mark objects that lie outside the SVG page
    """

    name = _("mark object outside page")

    def add_arguments(self, pars):
        pass

    def effect(self, clean=True):
        self.message("looking for objects lying outside the SVG page",
                     verbosity=3)
        self.init_artifact_layer()

        w = self.svg.unittouu(self.svg.viewport_width)
        h = self.svg.unittouu(self.svg.viewport_height)

        viewbox = inkex.BoundingBox((0, w), (0, h))

        counter = 0
        for elem in self.selected_or_all(skip_groups=True):

            desc = f"object with id={elem.get_id()} of type {elem.tag_name}"

            bb = self.bounding_box(elem)
            if not (bb & viewbox):
                counter += 1
                desc += " lies outside the page"
                self.message("\t-", desc, verbosity=2)
                self.outline_bounding_box(WARNING, elem, bb=bb, msg=desc)
                continue

        if clean:
            self.clean_artifacts(force=False)

        self.message(ngettext("{counter} object lies outside the SVG page",
                              "{counter} objects lie outside the SVG page",
                              counter).format(counter=counter),
                     verbosity=1)
        self.message(_("{extension:s}: running time = {time:.0f}ms")
                     .format(extension=self.name, time=self.get_timer()),
                     verbosity=3)
        self.message("",
                     verbosity=1)


if __name__ == '__main__':
    MarkOutside().run()
