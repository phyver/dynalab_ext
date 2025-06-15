#!/usr/bin/env python

import inkex

from lib import dynalab


class Ungroups(dynalab.Ext):
    """
    constantly changing dummy extension to test features for upcoming
    extensions
    Can serve as a basis for new extensions.
    """

    def add_arguments(self, pars):
        pars.add_argument("--remove-layers", type=inkex.Boolean,
                          default=True, help="remove layers",
                          dest="remove_layers")
        pars.add_argument("--remove-groups", type=inkex.Boolean,
                          default=True, help="remove groups",
                          dest="remove_groups")

    def effect(self):
        if not self.options.remove_layers and not self.options.remove_groups:
            self.abort("", "nothing to do: you must select to remove layers and/or groups")

        self.message("remove groups and layers in selection",
                     verbosity=3)

        # find all groups / layers in the selection
        groups = []
        counter_groups = 0
        counter_layers = 0
        for elem, tr in self.selected_or_all(skip_groups=False):

            if isinstance(elem, inkex.Layer):
                if self.options.remove_layers:
                    groups.append((elem, tr))
            elif isinstance(elem, inkex.Group):
                if self.options.remove_groups:
                    groups.append((elem, tr))

        # reverse the order, so that deeper groups are removed first
        groups.reverse()
        for gr, tr in groups:
            if gr.attrib.get("clip-path", "none") != "none":
                self.message(f"""
WARNING: group {gr.get('id')} contains a clip-path. This clip path is
discarded when ungrouping. If that is a problem, Undo (Ctrl-z) the ungrouping
and find a way to deal with that. (You can try ungrouping it manually, or try
using the "Arrange" => "deep-ungroup" extension.)
                """)
            if isinstance(gr, inkex.Layer):
                self.message("\t-", f"move elements out of layer with id={gr.get_id()}",
                             verbosity=2)
                counter_layers += 1
            elif isinstance(gr, inkex.Group):
                self.message("\t-", f"ungroup group with id={gr.get_id()}",
                             verbosity=2)
                counter_groups += 1

            for elem in gr:
                gr.remove(elem)
                elem.transform = tr @ gr.transform @ elem.transform
                self.svg.add(elem)
            gr.getparent().remove(gr)

        if self.options.remove_groups:
            self.message(f"{counter_groups} group(s) removed",
                         verbosity=1)
        if self.options.remove_layers:
            self.message(f"{counter_layers} layer(s) removed",
                         verbosity=1)
        self.message(f"remove groups: running time = {self.running_time():.0f}ms",
                     verbosity=3)
        self.message("",
                     verbosity=1)


if __name__ == '__main__':
    Ungroups().run()
