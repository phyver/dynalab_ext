#!/usr/bin/env python

from gettext import gettext as _
from gettext import ngettext

import inkex

from lib import dynalab
from lib.dynalab import WARNING


class MarkGroups(dynalab.Ext):
    """
    mark the bounding boxes of groups and layers
    """

    name = _("mark groups and layers")

    def add_arguments(self, pars):
        pars.add_argument("--mark-layers", type=inkex.Boolean, default=True, help="mark layers", dest="mark_layers")
        pars.add_argument("--mark-groups", type=inkex.Boolean, default=True, help="mark groups", dest="mark_groups")

    def effect(self, clean=True):
        if not self.options.mark_layers and not self.options.mark_groups:
            self.abort("", "nothing to do: you must select to mark layers and/or groups")

        self.message(self.name, verbosity=3)
        self.init_artifact_layer()

        counter_groups = 0
        counter_layers = 0
        for elem in self.selected_or_all(skip_groups=False):

            if isinstance(elem, inkex.Layer):
                if self.options.mark_layers:
                    desc = _("object with id={id} is a layer").format(id=elem.get_id())
                    counter_layers += 1
                    self.message("\t-", desc, verbosity=2)
                    w = self.config["artifacts_stroke_width"]
                    self.outline_bounding_box(WARNING, elem, stroke_width=w / 2, stroke_dasharray=f"{w},{w}", msg=desc)

            elif isinstance(elem, inkex.Group):
                if self.options.mark_groups:
                    desc = _("object with id={id} is a group").format(id=elem.get_id())
                    counter_groups += 1
                    self.message("\t-", desc, verbosity=2)
                    w = self.config["artifacts_stroke_width"]
                    self.outline_bounding_box(WARNING, elem, stroke_width=w / 2, msg=desc)

        if clean:
            self.clean_artifacts(force=False)

        if self.options.mark_groups:
            counter = counter_groups
            self.message(
                ngettext("{counter} group found", "{counter} groups found", counter).format(counter=counter),
                verbosity=1,
            )
        if self.options.mark_layers:
            counter = counter_layers
            self.message(
                ngettext("{counter} layer found", "{counter} layers found", counter).format(counter=counter),
                verbosity=1,
            )
        self.message(
            _("{extension:s}: running time = {time:.0f}ms").format(extension=self.name, time=self.get_timer()),
            verbosity=3,
        )
        self.message("", verbosity=1)


if __name__ == "__main__":
    MarkGroups().run()
