#!/usr/bin/env python

from collections import defaultdict
from gettext import gettext as _
from gettext import ngettext

import inkex

from lib import dynalab


class MiscPalettes(dynalab.Ext):
    """
    display small squares with border / fill for each border color and fill
    color of selected objects
    """

    name = _("border and fill palettes")

    def add_arguments(self, pars):
        pars.add_argument("--stroke", type=inkex.Boolean, default=True, help="look for stroke colors")
        pars.add_argument("--fill", type=inkex.Boolean, default=True, help="look for fill colors")

    def effect(self, clean=True):
        self.message("looking for stroke colors", verbosity=3)
        self.init_artifact_layer()

        if not self.options.stroke and not self.options.fill:
            self.abort(_("choose at least one of stroke / fill color"))

        stroke_colors = defaultdict(set)
        fill_colors = defaultdict(set)

        for elem in self.selected_or_all(skip_groups=True):
            if self.options.stroke:
                c = elem.style.get("stroke")
                if c is not None and c != "none" and not c.startswith("url("):
                    # FIXME: should I do something with "none" strokes
                    stroke_colors[c].add(elem.get_id())

            if self.options.fill:
                c = elem.style.get("fill")
                if c is not None and c != "none" and not c.startswith("url("):
                    # FIXME: should I do something with "none" fill
                    fill_colors[c].add(elem.get_id())

        artifact_layer = self.svg.getElementById(dynalab.ARTIFACT_LAYER_ID)
        side = self.mm_to_svg(10)  # side of representing square
        w = self.mm_to_svg(1)  # stroke width of representing square

        x = 0  # current representing square position
        y = 0  # ...

        if self.options.stroke:
            x = 0
            y -= 2 * side
            for c in sorted(stroke_colors.keys()):
                rect = inkex.Rectangle.new(x, y, side, side)
                rect.set("class", dynalab.ARTIFACT_CLASS)
                x += 1.5 * side
                rect.style = inkex.Style(
                    {
                        "stroke": c,
                        "fill": c,
                        "fill-opacity": 0.25,
                        "stroke-width": w,
                    }
                )
                artifact_layer.add(rect)

        if self.options.fill:
            x = 0
            y -= 2 * side
            for c in sorted(fill_colors.keys()):
                rect = inkex.Rectangle.new(x, y, side, side)
                rect.set("class", dynalab.ARTIFACT_CLASS)
                x += 1.5 * side
                rect.style = inkex.Style(
                    {
                        "fill": c,
                        "stroke": c,
                        "stroke-opacity": 0.25,
                        "stroke-width": w,
                    }
                )
                artifact_layer.add(rect)

        if clean:
            self.clean_artifacts(force=False)

        if self.options.stroke:
            counter = len(stroke_colors)
            self.message(
                ngettext("{counter} stroke color found", "{counter} stroke colors found", counter).format(
                    counter=counter
                ),
                verbosity=1,
            )
        if self.options.fill:
            counter = len(fill_colors)
            self.message(
                ngettext("{counter} fill color found", "{counter} fill colors found", counter).format(counter=counter),
                verbosity=1,
            )

        self.message(
            _("{extension:s}: running time = {time:.0f}ms").format(extension=self.name, time=self.get_timer()),
            verbosity=3,
        )
        self.message("", verbosity=1)


if __name__ == "__main__":
    MiscPalettes().run()
