#!/usr/bin/env python

import inkex

from lib import dynalab
from lib.dynalab import WARNING


class MarkGroups(dynalab.Ext):
    """
    show the bounding boxes of groups and layers found in the document
    """

    def add_arguments(self, pars):
        pars.add_argument("--mark-layers", type=inkex.Boolean,
                          default=True, help="mark layers",
                          dest="mark_layers")
        pars.add_argument("--mark-groups", type=inkex.Boolean,
                          default=True, help="mark groups",
                          dest="mark_groups")

    def effect(self, clean=True):
        if not self.options.mark_layers and not self.options.mark_groups:
            self.abort("", "nothing to do: you must select to mark layers and/or groups")

        self.message("looking for groups and/or layers",
                     verbosity=3)
        self.init_artifact_layer()

        counter_groups = 0
        counter_layers = 0
        for elem in self.selected_or_all(skip_groups=False):

            if isinstance(elem, inkex.Layer):
                if self.options.mark_layers:
                    desc = f"object with id={elem.get_id()} is a layer"
                    counter_layers += 1
                    self.message("\t-", desc, verbosity=2)
                    w = self.config["artifacts_stroke_width"]
                    self.outline_bounding_box(WARNING, elem,
                                              stroke_width=w/2,
                                              stroke_dasharray=f"{w},{w}",
                                              msg=desc)

            elif isinstance(elem, inkex.Group):
                if self.options.mark_groups:
                    desc = f"object witd id={elem.get_id()} is a group"
                    counter_groups += 1
                    self.message("\t-", desc, verbosity=2)
                    w = self.config["artifacts_stroke_width"]
                    self.outline_bounding_box(WARNING, elem,
                                              stroke_width=w/2,
                                              msg=desc)

        if clean:
            self.clean_artifacts(force=False)

        if self.options.mark_groups:
            self.message(f"{counter_groups} group(s) found",
                         verbosity=1)
        if self.options.mark_layers:
            self.message(f"{counter_layers} layer(s) found",
                         verbosity=1)
        self.message(f"looking for groups and layers: running time = {self.running_time():.0f}ms",
                     verbosity=3)
        self.message("",
                     verbosity=1)


if __name__ == '__main__':
    MarkGroups().run()
