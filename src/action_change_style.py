#!/usr/bin/env python

from gettext import gettext as _
import inkex

from lib import artefacts


class ChangeStyle(artefacts.Ext):
    """
    apply some new style (stroke-width, color and fill-color) to the selection
    """

    def add_arguments(self, pars):
        # TODO: add opacity argument
        pars.add_argument("--stroke-width", type=float,
                          default=-1, dest="stroke_width",
                          help=_("stroke width (mm)"))
        pars.add_argument("--stroke", type=str, default="#000000", help=_("stroke color"))
        pars.add_argument("--fill", type=str, default="none", help=_("fill color"))

    def effect(self):
        if not self.svg.selected:
            raise inkex.AbortExtension("\n\n" + _("You must select at least one element.") + "\n\n")

        if self.options.stroke_width < 0:
            self.options.stroke_width = self.config.get("laser_diameter", 0.2)
        if not self.options.stroke:
            self.options.stroke = "none"
        if not self.options.fill:
            self.options.fill = "none"

        if self.options.stroke == "CUT_MODE":
            self.options.stroke = self.config.get("laser_mode_cut_color", "#ff0000")
        elif self.options.stroke == "FILL_MODE":
            self.options.stroke = self.config.get("laser_mode_fill_color", "#0000ff")
        elif self.options.stroke == "LINE_MODE":
            self.options.stroke = self.config.get("laser_mode_line_color", "#000000")

        # TODO should I apply to all elements if the selection is empty?
        # TODO should I tag text blocks
        self.options.stroke_width = self.mm_to_svg(self.options.stroke_width)
        for elem, tr in self.selected_or_all(recurse=True,
                                             skip_groups=True,
                                             limit=None):
            elem.style["stroke"] = self.options.stroke
            elem.style["stroke-width"] = self.options.stroke_width
            elem.style["fill"] = self.options.fill


if __name__ == '__main__':
    ChangeStyle().run()
