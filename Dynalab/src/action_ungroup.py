#!/usr/bin/env python

from gettext import gettext as _
from gettext import ngettext

import inkex

from lib import dynalab


class Ungroups(dynalab.Ext):
    """
    ungroup objects
    """

    name = _("ungroup objects")

    def add_arguments(self, pars):
        pars.add_argument(
            "--remove-layers", type=inkex.Boolean, default=True, help="remove layers", dest="remove_layers"
        )
        pars.add_argument(
            "--remove-groups", type=inkex.Boolean, default=True, help="remove groups", dest="remove_groups"
        )

    def effect(self):
        if not self.options.remove_layers and not self.options.remove_groups:
            self.abort("", "nothing to do: you must select to remove layers and/or groups")

        self.message("remove groups and layers in selection", verbosity=3)

        # find all groups / layers in the selection
        groups = []
        counter_groups = 0
        counter_layers = 0
        for elem in self.selected_or_all(skip_groups=False):

            if isinstance(elem, inkex.Layer):
                if self.options.remove_layers:
                    groups.append(elem)
            elif isinstance(elem, inkex.Group):
                if self.options.remove_groups:
                    groups.append(elem)

        # reverse the order, so that deeper groups are removed first
        groups.reverse()
        for gr in groups:
            if gr.attrib.get("clip-path", "none") != "none":
                self.message(
                    f"""
WARNING: group {gr.get('id')} contains a clip-path. This clip path is
discarded when ungrouping. If that is a problem, Undo (Ctrl-z) the ungrouping
and find a way to deal with that. (You can try ungrouping it manually, or try
using the "Arrange" => "deep-ungroup" extension.)
                """
                )
            if isinstance(gr, inkex.Layer):
                self.message("\t-", f"move elements out of layer with id={gr.get_id()}", verbosity=2)
                counter_layers += 1
            elif isinstance(gr, inkex.Group):
                self.message("\t-", f"ungroup group with id={gr.get_id()}", verbosity=2)
                counter_groups += 1

            for elem in gr:
                gr.remove(elem)
                elem.transform = gr.getparent().composed_transform() @ gr.transform @ elem.transform
                self.svg.add(elem)
            gr.getparent().remove(gr)

        if self.options.remove_groups:
            counter = counter_groups
            self.message(
                ngettext("{counter} group removed", "{counter} groups removed", counter).format(counter=counter),
                verbosity=1,
            )
        if self.options.remove_layers:
            counter = counter_layers
            self.message(
                ngettext("{counter} layer removed", "{counter} layers removed", counter).format(counter=counter),
                verbosity=1,
            )
        self.message(
            _("{extension:s}: running time = {time:.0f}ms").format(extension=self.name, time=self.get_timer()),
            verbosity=3,
        )
        self.message("", verbosity=1)


if __name__ == "__main__":
    Ungroups().run()
