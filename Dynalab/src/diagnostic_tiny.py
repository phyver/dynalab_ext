#!/usr/bin/env python

import inkex

from lib import dynalab
from lib.dynalab import ERROR


class MarkTiny(dynalab.Ext):
    """
    tags the "tiny" elements found in the document
    """

    def add_arguments(self, pars):
        pars.add_argument("--size-tiny-element", type=float, dest="size_tiny_element",
                          help="size for tiny elements (mm)")

    def effect(self, clean=True):
        self.message("looking for tiny objects",
                     verbosity=3)
        self.init_artifact_layer()
        tiny = self.options.size_tiny_element or self.config["size_tiny_element"]

        # mark the selected elements
        counter = 0
        for elem, tr in self.selected_or_all(skip_groups=True):
            if isinstance(elem, inkex.TextElement):
                # TODO should I do something? computing the size requires
                # calling the slow inkscape_boundingbox method...
                # what about clones?
                continue
            bb = self.bounding_box(elem)
            if self.svg_to_mm(bb.width) < tiny and self.svg_to_mm(bb.height) < tiny:
                desc = f"object with id={elem.get_id()} of type {elem.tag_name} is 'tiny'"
                counter += 1
                self.message("\t-", desc, verbosity=2)
                self.outline_arrow(ERROR, elem, tr, msg=desc)
                self.outline_bounding_box(ERROR, elem, tr, stroke_width=0.1, msg=desc)

        if clean:
            self.clean(force=False)

        self.message(f"{counter} tiny object(s) found",
                     verbosity=1)
        self.message(f"looking for tiny objects: running time = {self.running_time():.0f}ms",
                     verbosity=3)
        self.message("",
                     verbosity=1)


if __name__ == '__main__':
    MarkTiny().run()
