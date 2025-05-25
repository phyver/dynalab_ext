#!/usr/bin/env python

import inkex

from lib import fablab


class DetectGroups(fablab.Ext):
    """
    show the bounding boxes of groups and layers found in the document
    """

    def __init__(self, show_layers=True, show_groups=True):
        super().__init__()
        self.show_layers = show_layers
        self.show_groups = show_groups

    def add_arguments(self, pars):
        pass

    def effect(self):
        self.init_error_layer()

        for elem, tr in self.selected_or_all(recurse=True,
                                             skip_groups=False,
                                             limit=None):

            if isinstance(elem, inkex.Layer):
                if self.show_layers:
                    self.outline_bounding_box(elem, tr, margin=0,
                                              stroke="#f00", stroke_width=".3mm",
                                              stroke_dasharray=".3mm, .3mm",
                                              msg=f"#{elem.get_id()}")

            elif isinstance(elem, inkex.Group):
                if self.show_groups:
                    self.outline_bounding_box(elem, tr, margin=0,
                                              stroke="#f00", stroke_width=".1mm",
                                              msg=f"#{elem.get_id()}")


if __name__ == '__main__':
    DetectGroups().run()
