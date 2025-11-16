#!/usr/bin/env python

from gettext import gettext as _
from gettext import ngettext

import inkex

from diagnostic_clones import MarkClones
from diagnostic_effects import MarkEffects
from diagnostic_groups import MarkGroups
from diagnostic_images import MarkImages
from diagnostic_open_paths import MarkOpenPaths
from diagnostic_outside_page import MarkOutside
from diagnostic_shapes import MarkShapes
from diagnostic_text import MarkText
from diagnostic_tiny import MarkTiny
from lib import dynalab

EXTENSIONS = {
    "non_paths": [MarkText, MarkImages, MarkShapes, MarkClones, MarkEffects],
    "groups": [MarkGroups],
    "tiny": [MarkTiny],
    "outside_objects": [MarkOutside],
    "open_paths": [MarkOpenPaths],
}


class Battery(dynalab.Ext):
    """
    battery of simple diagnostics run sequentially
    """

    name = _("diagnostics")

    def add_arguments(self, pars):
        pars.add_argument(
            "--non-paths", type=inkex.Boolean, default=True, help="mark non path objets", dest="non_paths"
        )
        pars.add_argument("--tiny", type=inkex.Boolean, default=True, help="mark tiny elements")
        pars.add_argument("--groups", type=inkex.Boolean, default=True, help="mark groups, layers and symbols")
        pars.add_argument(
            "--outside-objects",
            type=inkex.Boolean,
            default=True,
            help="mark objects outside the page",
            dest="outside_objects",
        )
        pars.add_argument("--open-paths", type=inkex.Boolean, default=True, help="mark open paths", dest="open_paths")

        for Ext in EXTENSIONS.values():
            for ext in Ext:
                inst = ext(reset_artifacts=False)
                inst.add_arguments(pars)

    def effect(self):
        reset_artifacts = True
        inst = None
        counter = 0
        BB = {}
        for name, Ext in EXTENSIONS.items():
            if getattr(self.options, name):
                for ext in Ext:
                    inst = ext(reset_artifacts=reset_artifacts)
                    reset_artifacts = False
                    inst.options = self.options
                    inst.document = self.document
                    inst.svg = self.svg
                    inst.BB = BB
                    inst.effect(clean=False)
                    BB = inst.BB
                    counter += 1
        if inst:
            inst.clean_artifacts(force=False)

        self.message(
            ngettext(
                "{counter} diagnostic extension was run", "{counter} diagnostic extensions were run", counter
            ).format(counter=counter),
            verbosity=1,
        )
        self.message(
            _("{extension:s}: running time = {time:.0f}ms").format(extension=self.name, time=self.get_timer()),
            verbosity=3,
        )
        self.message("", verbosity=1)


if __name__ == "__main__":
    Battery().run()
