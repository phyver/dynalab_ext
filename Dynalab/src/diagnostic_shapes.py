#!/usr/bin/env python

from gettext import gettext as _
from gettext import ngettext

import inkex

from lib import dynalab
from lib.dynalab import OK


class MarkShapes(dynalab.Ext):
    """
    mark non vectorized shapes
    """

    name = _("mark shapes")

    def add_arguments(self, pars):
        pass

    def effect(self, clean=True):
        self.message(self.name, verbosity=3)
        self.init_artifact_layer()

        counter = 0
        for elem in self.selected_or_all(skip_groups=True):
            desc = _("object with id={id} of type {tag}").format(id=elem.get_id(), tag=elem.tag_name)
            if isinstance(
                elem, (inkex.Line, inkex.Polyline, inkex.Polygon, inkex.Rectangle, inkex.Ellipse, inkex.Circle)
            ):
                desc += " " + _("is a simple shape")
                counter += 1
                self.message("\t-", desc, verbosity=2)
                self.outline_bounding_box(OK, elem, msg=desc)
                continue

        if clean:
            self.clean_artifacts(force=False)

        self.message(
            ngettext("{counter} shape found", "{counter} shapes found", counter).format(counter=counter), verbosity=1
        )
        self.message(
            _("{extension:s}: running time = {time:.0f}ms").format(extension=self.name, time=self.get_timer()),
            verbosity=3,
        )
        self.message("", verbosity=1)


if __name__ == "__main__":
    MarkShapes().run()
