#!/usr/bin/env python

import inkex

from lib import dynalab
from lib.dynalab import ERROR


class MarkImages(dynalab.Ext):
    """
    mark image objects
    """

    def add_arguments(self, pars):
        pass

    def effect(self, clean=True):
        self.message("looking for image objects",
                     verbosity=3)
        self.init_artifact_layer()

        counter = 0
        for elem in self.selected_or_all(skip_groups=True):
            desc = f"object with id={elem.get_id()} of type {elem.tag_name}"
            if isinstance(elem, inkex.Image):
                desc += " is a non vectorized image"
                counter += 1
                self.message("\t-", desc, verbosity=2)
                self.outline_bounding_box(ERROR, elem, msg=desc)
                continue

        if clean:
            self.clean_artifacts(force=False)

        self.message(f"{counter} image(s) found",
                     verbosity=1)
        self.message(f"looking for images: running time = {self.running_time():.0f}ms",
                     verbosity=3)
        self.message("",
                     verbosity=1)


if __name__ == '__main__':
    MarkImages().run()
