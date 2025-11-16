#!/usr/bin/env python

from gettext import gettext as _

import inkex

from lib import dynalab


class CloseOpen(dynalab.Ext):
    """
    close open subpaths whose endpoints are close
    """

    name = _("close open paths")

    def add_arguments(self, pars):
        pars.add_argument(
            "--close-distance",
            type=float,
            default=5,
            help="distance under which we close open path (mm)",
            dest="close_distance",
        )
        pars.add_argument(
            "--only-fill-mode-paths",
            type=inkex.Boolean,
            default=True,
            help="restrict to paths with 'fill mode' color",
            dest="only_fill_mode_paths",
        )

    def effect(self):
        if not self.svg.selected:
            self.abort(_("You must select at least one object."))

        self.message(f"close subpaths in selection, close_distance={self.options.close_distance}mm", verbosity=3)

        counter_paths = 0
        counter_subpaths_closed = 0
        counter_subpaths_not_closed = 0
        d = self.mm_to_svg(self.options.close_distance)
        d2 = d * d
        for elem in self.selected_or_all(skip_groups=False):

            # skip non-path element
            if not isinstance(elem, inkex.PathElement):
                continue

            # skip path that don't have the appropriate color
            if self.options.only_fill_mode_paths and elem.style.get("stroke") != self.config["laser_mode_fill_color"]:
                continue

            # skip paths with path effects
            if elem.get("inkscape:path-effect") is not None:
                self.message("\t-", "path with id={elem.get_id()} uses path effects, SKIP", verbosity=1)
                continue  # don't try closing them

            path = elem.path.to_absolute()
            coord = [p.end_point for p in path.proxy_iterator()]

            new_path = []
            i_start = -1
            c = 0  # counter for closed subpath
            for i, cmd in enumerate(path):
                x1, y1 = coord[i].x, coord[i].y
                if isinstance(cmd, inkex.paths.Move):  # start of new subpath
                    if i_start >= 0 and not isinstance(new_path[-1], inkex.paths.ZoneClose):
                        # this subpath is not closed, close it if distance is small enough
                        x0, y0 = coord[i_start].x, coord[i_start].y
                        x1, y1 = coord[i].x, coord[i].y
                        if (x0 - x1) * (x0 - x1) + (y0 - y1) * (y0 - y1) <= d2:
                            counter_subpaths_closed += 1
                            new_path.append(inkex.paths.ZoneClose())
                            c += 1
                        else:
                            counter_subpaths_not_closed += 1

                    i_start = i  # start of new path
                new_path.append(cmd)

            # deal with last element
            if not isinstance(new_path[-1], inkex.paths.ZoneClose):
                # this subpath is not closed, close it if distance is small enough
                x0, y0 = coord[i_start].x, coord[i_start].y
                x1, y1 = coord[i].x, coord[i].y
                if (x0 - x1) * (x0 - x1) + (y0 - y1) * (y0 - y1) <= d2:
                    counter_subpaths_closed += 1
                    new_path.append(inkex.paths.ZoneClose())
                    c += 1
                else:
                    counter_subpaths_not_closed += 1

            if c > 0:
                self.message("\t-", f"path with id={elem.get_id()}: {c} subpath(s) closed", verbosity=2)
                elem.path = new_path
                counter_paths += 1

        self.message(
            f"{counter_subpaths_closed} subpath(s) were closed in {counter_paths} path(s)",
            "\n",
            f"{counter_subpaths_not_closed} subpath(s) remained open their endpoints were too far away",
            verbosity=1,
        )
        self.message(
            _("{extension:s}: running time = {time:.0f}ms").format(extension=self.name, time=self.get_timer()),
            verbosity=3,
        )
        self.message("", verbosity=1)


if __name__ == "__main__":
    CloseOpen().run()
