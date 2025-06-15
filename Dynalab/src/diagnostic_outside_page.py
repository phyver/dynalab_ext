#!/usr/bin/env python

import inkex

from lib import dynalab
from lib.dynalab import WARNING


class MarkOutside(dynalab.Ext):

    def add_arguments(self, pars):
        pass

    def effect(self, clean=True):
        self.message("looking for objects lying outside the SVG page",
                     verbosity=3)
        self.init_artefact_layer()

        w = self.svg.unittouu(self.svg.viewport_width)
        h = self.svg.unittouu(self.svg.viewport_height)

        viewbox = inkex.BoundingBox((0, w), (0, h))

        missing_bbs = []

        counter = 0
        for elem, tr in self.selected_or_all(skip_groups=True):

            desc = f"object with id={elem.get_id()} of type {elem.tag_name}"

            if isinstance(elem, (inkex.TextElement, inkex.Use)):
                missing_bbs.append((elem, desc))
                continue

            bb = elem.bounding_box(transform=tr)
            if not (bb & viewbox):
                counter += 1
                desc += " lies outside the page"
                self.message("\t-", desc, verbosity=2)
                self.outline_bounding_box(WARNING, elem, tr=None, bb=bb, msg=desc)
                continue

        if missing_bbs:
            elems, descs = zip(*missing_bbs)
            bbs = self.get_inkscape_bboxes(*elems)
            for elem, bb, desc in zip(elems, bbs, descs):
                if not (bb & viewbox):
                    counter += 1
                    desc += " lies outside the page"
                    self.message("\t-", desc, verbosity=2)
                    self.outline_bounding_box(WARNING, elem, tr=None, bb=bb, msg=desc)

        if clean:
            self.clean(force=False)

        self.message(f"{counter} object(s) lie outside the SVG page",
                     verbosity=1)
        self.message(f"looking for object(s) outside the page: running time = {self.running_time():.0f}ms",
                     verbosity=3)
        self.message("",
                     verbosity=1)


if __name__ == '__main__':
    MarkOutside().run()
