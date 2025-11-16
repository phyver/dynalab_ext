#!/usr/bin/env python

from gettext import gettext as _
from gettext import ngettext

import inkex

from lib import dynalab
from lib.dynalab import WARNING


class MarkOpenPaths(dynalab.Ext):
    """
    mark paths with open subpaths
    """

    name = _("mark open paths")

    def add_arguments(self, pars):
        pars.add_argument(
            "--only-fill-mode-paths",
            type=inkex.Boolean,
            default=True,
            help="restrict to paths with 'fill mode' color",
            dest="only_fill_mode_paths",
        )

    def effect(self, clean=True):
        self.message(self.name, verbosity=3)
        self.init_artifact_layer()

        counter_paths = 0
        counter_subpaths = 0
        for elem in self.selected_or_all(skip_groups=False):
            # skip non-path element
            if not isinstance(elem, inkex.PathElement):
                continue
            # skip path that don't have the appropriate color
            if self.options.only_fill_mode_paths and elem.style.get("stroke") != self.config["laser_mode_fill_color"]:
                continue

            # skip paths with path effects
            if elem.get("inkscape:path-effect") is not None:
                self.message(
                    "\t-", _("path with id={id} uses path effects, SKIP").format(id=elem.get_id()), verbosity=1
                )
                continue

            prev = None
            c = 0  # counter for open subpaths
            for cmd in elem.path:
                if isinstance(cmd, (inkex.paths.move, inkex.paths.Move)):  # start of new subpath
                    if prev is not None and not isinstance(prev, (inkex.paths.zoneClose, inkex.paths.ZoneClose)):
                        # this subpath is not closed
                        c += 1
                        counter_subpaths += 1
                prev = cmd
            if prev is not None and not isinstance(prev, (inkex.paths.zoneClose, inkex.paths.ZoneClose)):
                # the final subpath is not closed
                c += 1
            if c > 0:
                desc = _("object with id={id} of type {tag}").format(id=elem.get_id(), tag=elem.tag_name)
                desc += " " + ngettext("contains {counter} open subpath", "contains {counter} open subpaths", c).format(
                    counter=c
                )
                counter_paths += 1
                self.message("\t-", desc, verbosity=2)
                self.outline_bounding_box(WARNING, elem, msg=desc)

        if clean:
            self.clean_artifacts(force=False)

        "{counter_subpaths} open subpath(s) found inside {counter_paths} path object(s)"
        self.message(
            ngettext("{counter} open subpath found", "{counter} open subpaths found", counter_subpaths).format(
                counter=counter_subpaths
            ),
            ngettext("inside {counter} path object", "inside {counter} path objects", counter_paths).format(
                counter=counter_paths
            ),
            verbosity=1,
        )
        self.message(
            _("{extension:s}: running time = {time:.0f}ms").format(extension=self.name, time=self.get_timer()),
            verbosity=3,
        )
        self.message("", verbosity=1)


if __name__ == "__main__":
    MarkOpenPaths().run()
