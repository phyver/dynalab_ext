#!/usr/bin/env python

from gettext import gettext as _

import inkex

from lib import artefacts


class MarkOpen(artefacts.Ext):
    def add_arguments(self, pars):
        pars.add_argument("--close-distance", type=float,
                          default=5, help="distance under which we close open path (mm)",
                          dest="close_distance")
        pars.add_argument("--only-fill-mode-paths", type=inkex.Boolean,
                          default=True, help="restrict to paths with 'fill mode' color",
                          dest="only_fill_mode_paths")

    def effect(self):
        if not self.svg.selected:
            raise inkex.AbortExtension("\n\n" + _("You must select at least one element.") + "\n\n")

        for elem, tr in self.selected_or_all(recurse=True,
                                             skip_groups=False,
                                             limit=None):

            # skip non-path element
            if not isinstance(elem, inkex.PathElement):
                continue

            # skip path that don't have the appropriate color
            if self.options.only_fill_mode_paths and elem.style.get("stroke") != self.config["laser_mode_fill_color"]:
                continue

            d = self.mm_to_svg(self.options.close_distance)
            d2 = d*d

            path = elem.path.to_absolute()
            coord = [p.end_point for p in path.proxy_iterator()]

            new_path = []
            i_start = 0
            modified = False
            for i, cmd in enumerate(path):
                if isinstance(cmd, inkex.paths.Move):     # start of new subpath
                    if i_start > 0 and not isinstance(new_path[-1], inkex.paths.ZoneClose):
                        # this subpath is not closed, close it if distance is small enough
                        x0, y0 = coord[i_start].x, coord[i_start].y
                        x1, y1 = coord[i].x, coord[i].y
                        if (x0-x1)*(x0-x1) + (y0-y1)*(y0-y1) <= d2:
                            new_path.append(inkex.paths.ZoneClose())
                            modified = True
                    i_start = i         # start of new path
                new_path.append(cmd)

            # deal with last element
            if not isinstance(new_path[-1], inkex.paths.ZoneClose):
                # this subpath is not closed, close it if distance is small enough
                x0, y0 = coord[i_start].x, coord[i_start].y
                x1, y1 = coord[i].x, coord[i].y
                if (x0-x1)*(x0-x1) + (y0-y1)*(y0-y1) <= d2:
                    new_path.append(inkex.paths.ZoneClose())
                    modified = True

            if modified:
                elem.path = new_path


if __name__ == '__main__':
    MarkOpen().run()
