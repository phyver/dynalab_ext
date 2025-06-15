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
        self.message("looking for open paths",
                     verbosity=3)
        self.init_artefact_layer()

        counter_paths = 0
        counter_subpaths = 0
        for elem, tr in self.selected_or_all(skip_groups=False):
            # skip non-path element
            if not isinstance(elem, inkex.PathElement):
                continue
            # skip path that don't have the appropriate color
            if self.options.only_fill_mode_paths and elem.style.get("stroke") != self.config["laser_mode_fill_color"]:
                continue

            # skip paths with path effects
            if elem.get("inkscape:path-effect") is not None:
                # FIXME: should I display a warning message
                continue

            prev = None
            c = 0       # counter for open subpaths
            for cmd in elem.path:
                if isinstance(cmd, (inkex.paths.move, inkex.paths.Move)):     # start of new subpath
                    if prev is not None and not isinstance(prev, (inkex.paths.zoneClose, inkex.paths.ZoneClose)):
                        # this subpath is not closed
                        c += 1
                        counter_subpaths += 1
                prev = cmd
            if prev is not None and not isinstance(prev, (inkex.paths.zoneClose, inkex.paths.ZoneClose)):
                # the final subpath is not closed
                c += 1
            if c > 0:
                desc = f"path with id={elem.get_id()} contains {c} open subpath(s)"
                counter_paths += 1
                self.message("\t-", desc, verbosity=2)
                self.outline_bounding_box(WARNING, elem, tr, msg=desc)

        if clean:
            self.clean(force=False)

        self.message(f"{counter_subpaths} open subpath(s) found inside {counter_paths} path object(s) found",
                     verbosity=1)
        self.message(f"looking for open paths: running time = {self.running_time():.0f}ms",
                     verbosity=3)
        self.message("",
                     verbosity=1)


if __name__ == '__main__':
    MarkOpenPaths().run()
