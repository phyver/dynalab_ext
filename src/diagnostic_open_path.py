#!/usr/bin/env python

import re
import inkex

from lib import artefacts
from lib.artefacts import WARNING


class MarkOpen(artefacts.Ext):
    def add_arguments(self, pars):
        pars.add_argument("--all-path", type=inkex.Boolean,
                          default=False, help="don't restrict to path with 'fill mode' color",
                          dest="all_path")

    def effect(self, clean=True):
        self.init_artefact_layer()

        for elem, tr in self.selected_or_all(recurse=True,
                                             skip_groups=False,
                                             limit=None):

            tag = re.sub(r'^\{.*\}', '', elem.tag)
            desc = f"#{elem.get_id()} ({tag})"

            # skip non-path element
            if not isinstance(elem, inkex.PathElement):
                continue

            # skip path that don't have the appropriate color (unless option "all_path" was given)
            if not self.options.all_path and elem.style.get("stroke") != self.config["laser_mode_fill_color"]:
                continue

            prev = None
            for cmd in elem.path:
                if isinstance(cmd, (inkex.paths.move, inkex.paths.Move)):     # start of new subpath
                    if prev is not None and not isinstance(prev, (inkex.paths.zoneClose, inkex.paths.ZoneClose)):
                        # this subpath is not closed, mark it
                        self.outline_bounding_box(WARNING, elem, tr, msg=desc)
                        break
                prev = cmd
            if prev is not None and not isinstance(prev, (inkex.paths.zoneClose, inkex.paths.ZoneClose)):
                # this subpath is not closed, mark it
                self.outline_bounding_box(WARNING, elem, tr, msg=desc)

        if clean:
            self.clean(force=False)


if __name__ == '__main__':
    MarkOpen().run()
