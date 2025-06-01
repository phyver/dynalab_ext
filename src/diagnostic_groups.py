#!/usr/bin/env python

import inkex

from lib import dynalab
from lib.dynalab import WARNING


class MarkGroups(dynalab.Ext):
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
        if not self.show_layers and not self.show_groups:
            self.abort("", "nothing to do: you must select to mark layers and/or groups")

        self.message("looking for groups and/or layers",
                     verbosity=3)
        self.init_artefact_layer()

        # TODO: config option to use get_inkscape_bboxes for bounding boxes?
        group_counter = 0
        layer_counter = 0
        for elem, tr in self.selected_or_all(recurse=True,
                                             skip_groups=False,
                                             limit=None):

            if isinstance(elem, inkex.Layer):
                if self.show_layers:
                    desc = f"object with id={elem.get_id()} is a layer"
                    layer_counter += 1
                    self.message("\t-", desc, verbosity=2)
                    self.outline_bounding_box(WARNING, elem, tr, margin=0,
                                              stroke_width=".7mm",
                                              stroke_dasharray=".7mm, .7mm",
                                              msg=desc)

            elif isinstance(elem, inkex.Group):
                if self.show_groups:
                    desc = f"object witd id={elem.get_id()} is a group"
                    group_counter += 1
                    self.message("\t-", desc, verbosity=2)
                    self.outline_bounding_box(WARNING, elem, tr, margin=0,
                                              stroke_width=".3mm",
                                              msg=desc)

        if clean:
            self.clean(force=False)

        if self.show_groups:
            self.message(f"{group_counter} group(s) found",
                         verbosity=1)
        if self.show_layers:
            self.message(f"{layer_counter} layer(s) found",
                         verbosity=1)
        self.message(f"looking for groups and layers: running time = {self.running_time():.0f}ms",
                     verbosity=3)
        self.message("",
                     verbosity=1)


if __name__ == '__main__':
    MarkGroups().run()
