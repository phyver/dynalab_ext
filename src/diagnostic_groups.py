#!/usr/bin/env python

import inkex

from lib import artefacts
from lib.artefacts import WARNING


class MarkGroups(artefacts.Ext):
    """
    show the bounding boxes of groups and layers found in the document
    """

    def __init__(self, show_layers=True, show_groups=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.show_layers = show_layers
        self.show_groups = show_groups

    def add_arguments(self, pars):
        pass

    def effect(self, clean=True):
        self.init_artefact_layer()

        for elem, tr in self.selected_or_all(recurse=True,
                                             skip_groups=False,
                                             limit=None):

            if isinstance(elem, inkex.Layer):
                if self.show_layers:
                    self.outline_bounding_box(WARNING, elem, tr, margin=0,
                                              stroke_width=".7mm",
                                              stroke_dasharray=".7mm, .7mm",
                                              msg=f"#{elem.get_id()}")

            elif isinstance(elem, inkex.Group):
                if self.show_groups:
                    self.outline_bounding_box(WARNING, elem, tr, margin=0,
                                              stroke_width=".3mm",
                                              msg=f"#{elem.get_id()}")

        if clean:
            self.clean(force=False)


if __name__ == '__main__':
    MarkGroups().run()
