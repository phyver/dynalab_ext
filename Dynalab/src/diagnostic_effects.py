#!/usr/bin/env python

from gettext import gettext as _
from gettext import ngettext

from lib import dynalab, utils
from lib.dynalab import ERROR, WARNING


class MarkEffects(dynalab.Ext):
    """
    mark effects
    """

    name = _("mark objects with effects")

    def add_arguments(self, pars):
        pass

    def effect(self, clean=True):
        self.message(self.name, verbosity=3)
        self.init_artifact_layer()

        counter = 0
        for elem in self.selected_or_all(skip_groups=True):
            desc = _("object with id={id} of type {tag}").format(id=elem.get_id(), tag=elem.tag_name)

            E = utils.effects(elem)
            if not E:
                continue

            desc += " " + _("uses the following effect(s):") + " " + ", ".join(E)
            counter += 1
            self.message("\t-", desc, verbosity=2)

            if E == ["path-effect"]:
                # path effects can be transformed to real path, so we only
                # give them a WARNING level)
                self.outline_bounding_box(WARNING, elem, msg=desc)
            else:
                self.outline_bounding_box(ERROR, elem, msg=desc)

        if clean:
            self.clean_artifacts(force=False)

        self.message(
            ngettext("{counter} object with effect(s) found", "{counter} objects with effect(s) found", counter).format(
                counter=counter
            ),
            verbosity=1,
        )
        self.message(
            _("{extension:s}: running time = {time:.0f}ms").format(extension=self.name, time=self.get_timer()),
            verbosity=3,
        )
        self.message("", verbosity=1)


if __name__ == "__main__":
    MarkEffects().run()
