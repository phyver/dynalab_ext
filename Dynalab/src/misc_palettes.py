#!/usr/bin/env python

from collections import defaultdict

import inkex

from lib import dynalab


class MiscPalettes(dynalab.Ext):
    """
    constantly changing dummy extension to test features for upcoming
    extensions
    Can serve as a basis for new extensions.
    """

    def add_arguments(self, pars):
        pars.add_argument("--stroke", type=inkex.Boolean,
                          default=True, help="look for stroke colors")
        pars.add_argument("--fill", type=inkex.Boolean,
                          default=True, help="look for fill colors")

    def effect(self, clean=True):
        self.message("looking for stroke colors",
                     verbosity=3)
        self.init_artifact_layer()

        if not self.options.stroke and not self.options.fill:
            self.abort("choose at least one of stroke / fill color")

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
        side = self.mm_to_svg(10)       # side of representing square
        w = self.mm_to_svg(1)           # stroke width of representing square

        x = 0   # current representing square position
        y = 0   # ...

        if self.options.stroke:
            x = 0
            y -= 2*side
            for c in sorted(stroke_colors.keys()):
                rect = inkex.Rectangle.new(x, y, side, side)
                rect.set("class", dynalab.ARTIFACT_CLASS)
                x += 1.5*side
                rect.style = inkex.Style({
                    "stroke": c,
                    "fill": c,
                    "fill-opacity": 0.25,
                    "stroke-width": w,
                })
                artifact_layer.add(rect)

        if self.options.fill:
            x = 0
            y -= 2*side
            for c in sorted(fill_colors.keys()):
                rect = inkex.Rectangle.new(x, y, side, side)
                rect.set("class", dynalab.ARTIFACT_CLASS)
                x += 1.5*side
                rect.style = inkex.Style({
                    "fill": c,
                    "stroke": c,
                    "stroke-opacity": 0.25,
                    "stroke-width": w,
                })
                artifact_layer.add(rect)

        if clean:
            self.clean_artifacts(force=False)

        if self.options.stroke:
            self.message(f"{len(stroke_colors)} stroke color(s) found",
                         verbosity=1)
        if self.options.fill:
            self.message(f"{len(fill_colors)} fill color(s) found",
                         verbosity=1)

        self.message(f"looking for stroke and fill colors: running time = {self.running_time():.0f}ms",
                     verbosity=3)
        self.message("",
                     verbosity=1)


if __name__ == '__main__':
    MiscPalettes().run()
