#!/usr/bin/env python

import inkex

from lib import dynalab

from diagnostic_text import MarkText
from diagnostic_images import MarkImages
from diagnostic_shapes import MarkShapes
from diagnostic_clones import MarkClones
from diagnostic_effects import MarkEffects

from diagnostic_groups import MarkGroups

from diagnostic_tiny import MarkTiny
from diagnostic_open_paths import MarkOpenPaths
from diagnostic_outside_page import MarkOutside


EXTENSIONS = {
    "non_paths": [MarkText, MarkImages, MarkShapes, MarkClones, MarkEffects],
    "groups": [MarkGroups],
    "tiny": [MarkTiny],
    "outside_objects": [MarkOutside],
    "open_paths": [MarkOpenPaths],
}


class Battery(dynalab.Ext):
    """
    constantly changing dummy extension to test features for upcoming
    extensions
    Can serve as a basis for new extensions.
    """

    def add_arguments(self, pars):
        pars.add_argument("--non-paths", type=inkex.Boolean,
                          default=True, help="mark non path objets", dest="non_paths")
        pars.add_argument("--tiny", type=inkex.Boolean,
                          default=True, help="mark tiny elements")
        pars.add_argument("--groups", type=inkex.Boolean,
                          default=True, help="mark groups, layers and symbols")
        pars.add_argument("--outside-objects", type=inkex.Boolean,
                          default=True, help="mark objects outside the page", dest="outside_objects")
        pars.add_argument("--open-paths", type=inkex.Boolean,
                          default=True, help="mark open paths", dest="open_paths")

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

        self.message(f"{counter} diagnostic extension(s) were run",
                     verbosity=1)
        self.message(f"total running time = {self.running_time():.0f}ms",
                     verbosity=3)
        self.message("",
                     verbosity=1)


if __name__ == '__main__':
    Battery().run()
