#!/usr/bin/env python

import inkex

from lib import dynalab
from lib.dynalab import WARNING


class MarkOpenPaths(dynalab.Ext):
    def add_arguments(self, pars):
        pars.add_argument("--only-fill-mode-paths", type=inkex.Boolean,
                          default=True, help="restrict to paths with 'fill mode' color",
                          dest="only_fill_mode_paths")

    def effect(self, clean=True):
        self.init_artefact_layer()

        for elem, tr in self.selected_or_all(recurse=True,
                                             skip_groups=False,
                                             limit=None):

            desc = f"id={elem.get_id()} of type {elem.tag_name}"

            # skip non-path element
            if not isinstance(elem, inkex.PathElement):
                continue

            # skip path that don't have the appropriate color
            if self.options.only_fill_mode_paths and elem.style.get("stroke") != self.config["laser_mode_fill_color"]:
                continue

            prev = None
            for cmd in elem.path:
                if isinstance(cmd, (inkex.paths.move, inkex.paths.Move)):     # start of new subpath
                    if prev is not None and not isinstance(prev, (inkex.paths.zoneClose, inkex.paths.ZoneClose)):
                        # this subpath is not closed, mark it
                        desc += " => contains non-closed parts"
                        self.outline_bounding_box(WARNING, elem, tr, msg=desc)
                        break
                prev = cmd
            else:
                if prev is not None and not isinstance(prev, (inkex.paths.zoneClose, inkex.paths.ZoneClose)):
                    # this subpath is not closed, mark it
                    desc += " => contains non-closed parts"
                    self.outline_bounding_box(WARNING, elem, tr, msg=desc)

        if clean:
            self.clean(force=False)


if __name__ == '__main__':
    MarkOpenPaths().run()
