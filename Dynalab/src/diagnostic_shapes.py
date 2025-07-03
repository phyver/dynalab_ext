#!/usr/bin/env python

import inkex

from lib import dynalab
from lib.dynalab import OK


class MarkShapes(dynalab.Ext):
    """
    mark shapes
    """

    def add_arguments(self, pars):
        pass

    def effect(self, clean=True):
        self.message("looking for shapes",
                     verbosity=3)
        self.init_artifact_layer()

        counter = 0
        for elem in self.selected_or_all(skip_groups=True):
            desc = f"object with id={elem.get_id()} of type {elem.tag_name}"
            if isinstance(elem, (inkex.Line, inkex.Polyline, inkex.Polygon,
                                 inkex.Rectangle, inkex.Ellipse, inkex.Circle)):
                desc += " is a shape"
                counter += 1
                self.message("\t-", desc, verbosity=2)
                self.outline_bounding_box(OK, elem, msg=desc)
                continue

        if clean:
            self.clean_artifacts(force=False)

        self.message(f"{counter} shape(s) found",
                     verbosity=1)
        self.message(f"looking for shapes: running time = {self.get_timer():.0f}ms",
                     verbosity=3)
        self.message("",
                     verbosity=1)


if __name__ == '__main__':
    MarkShapes().run()
