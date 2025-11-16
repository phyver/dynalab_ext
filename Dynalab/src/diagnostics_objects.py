#!/usr/bin/env python

from gettext import gettext as _
from gettext import ngettext

import inkex

from diagnostic_clones import MarkClones
from diagnostic_effects import MarkEffects
from diagnostic_images import MarkImages
from diagnostic_shapes import MarkShapes
from diagnostic_text import MarkText
from lib import dynalab

EXTENSIONS = {
    "text": MarkText,
    "images": MarkImages,
    "shapes": MarkShapes,
    "clones": MarkClones,
    "effects": MarkEffects,
}


class Battery(dynalab.Ext):
    """
    battery of diagnostics to mark non vectorized objects
    """

    name = _("non vectorized objects")

    def add_arguments(self, pars):
        pars.add_argument("--text", type=inkex.Boolean, default=True, help="mark text objets")
        pars.add_argument("--images", type=inkex.Boolean, default=True, help="mark images")
        pars.add_argument("--shapes", type=inkex.Boolean, default=True, help="mark non-path shapes")
        pars.add_argument("--clones", type=inkex.Boolean, default=True, help="mark clones")
        pars.add_argument("--effects", type=inkex.Boolean, default=True, help="mark objects with effects")

        for ext in EXTENSIONS.values():
            inst = ext(reset_artifacts=False)
            inst.add_arguments(pars)

    def effect(self):
        reset_artifacts = True
        inst = None
        counter = 0
        bbs = {}
        for name, ext in EXTENSIONS.items():
            if getattr(self.options, name):
                inst = ext(reset_artifacts=reset_artifacts)
                reset_artifacts = False
                inst.options = self.options
                inst.document = self.document
                inst.svg = self.svg
                inst.bb = bbs
                inst.effect(clean=False)
                bbs = inst.bb
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
