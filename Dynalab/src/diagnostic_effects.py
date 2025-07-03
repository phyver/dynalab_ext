#!/usr/bin/env python

from lib import dynalab, utils
from lib.dynalab import WARNING, ERROR


class MarkEffects(dynalab.Ext):
    """
    mark effects
    """

    def add_arguments(self, pars):
        pass

    def effect(self, clean=True):
        self.message("looking for effects",
                     verbosity=3)
        self.init_artifact_layer()

        counter = 0
        for elem in self.selected_or_all(skip_groups=True):
            desc = f"object with id={elem.get_id()} of type {elem.tag_name}"

            E = utils.effects(elem)
            if not E:
                continue

            desc += " uses the following effect(s): " + ", ".join(E)
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

        self.message(f"{counter} clone(s) found",
                     verbosity=1)
        self.message(f"looking for clones: running time = {self.get_timer():.0f}ms",
                     verbosity=3)
        self.message("",
                     verbosity=1)


if __name__ == '__main__':
    MarkEffects().run()
