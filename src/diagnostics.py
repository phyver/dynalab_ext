#!/usr/bin/env python

import inkex

from lib import artefacts

from diagnostic_tiny import MarkTiny
from diagnostic_paths import MarkNonPaths
from diagnostic_groups import MarkGroups
from diagnostic_open_paths import MarkOpenPaths


EXTENSIONS = {
    "tiny": MarkTiny,
    "non_paths": MarkNonPaths,
    "groups": MarkGroups,
    "open_paths": MarkOpenPaths,
}


class Battery(artefacts.Ext):
    """
    constantly changing dummy extension to test features for upcoming
    extensions
    Can serve as a basis for new extensions.
    """

    def add_arguments(self, pars):
        pars.add_argument("--non-paths", type=inkex.Boolean,
                          default=True, help="mark non path objets", dest="non_paths")
        pars.add_argument("--groups", type=inkex.Boolean,
                          default=True, help="mark groups and layers")
        pars.add_argument("--tiny", type=inkex.Boolean,
                          default=True, help="detect tiny elements")
        pars.add_argument("--open-paths", type=inkex.Boolean,
                          default=True, help="mark open paths", dest="open_paths")

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
