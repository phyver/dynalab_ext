#!/usr/bin/env python

import inkex

from lib import artefacts

from diagnostic_tiny import MarkTiny
from diagnostic_shapes import MarkShapes
from diagnostic_groups import MarkGroups


EXTENSIONS = {
    "tiny": MarkTiny,
    "shapes": MarkShapes,
    "groups": MarkGroups,
}


class Battery(artefacts.Ext):
    """
    constantly changing dummy extension to test features for upcoming
    extensions
    Can serve as a basis for new extensions.
    """

    def add_arguments(self, pars):
        pars.add_argument("--tiny", type=inkex.Boolean,
                          default=True, help="detect tiny elements")
        pars.add_argument("--shapes", type=inkex.Boolean,
                          default=True, help="mark shapes")
        pars.add_argument("--groups", type=inkex.Boolean,
                          default=True, help="mark groups and layers")

        for ext in EXTENSIONS.values():
            inst = ext(reset_artefacts=False)
            inst.add_arguments(pars)

    def effect(self):
        c = 0
        reset_artefacts = True
        inst = None
        for name, ext in EXTENSIONS.items():
            if getattr(self.options, name):
                inst = ext(reset_artefacts=reset_artefacts)
                reset_artefacts = False
                inst.options = self.options
                inst.document = self.document
                inst.svg = self.svg
                inst.effect(clean=False)
                c += 1
        if inst:
            inst.clean(force=False)


if __name__ == '__main__':
    Battery().run()
