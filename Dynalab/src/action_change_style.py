#!/usr/bin/env python

from gettext import gettext as _

import inkex

from lib import dynalab, utils


class ChangeStyle(dynalab.Ext):
    """
    apply some new style (stroke-width, color and fill-color) to the selection
    """

    name = _("change style")

    def add_arguments(self, pars):
        pars.add_argument("--stroke-width", type=float, default=-1, dest="stroke_width", help="stroke width (mm)")
        pars.add_argument("--stroke", type=str, default="#000000", help="stroke color")
        pars.add_argument("--fill", type=str, default="none", help="fill color")
        pars.add_argument("--fill-opacity", type=float, default=100, help="opacity (%)", dest="fill_opacity")
        pars.add_argument("--extra-style", type=str, default="", help="extra style options")
        pars.add_argument(
            "--only-paths", type=inkex.Boolean, default=True, help="only apply to path like objects", dest="only_paths"
        )

    def effect(self):
        if not self.svg.selected:
            self.abort(_("You must select at least one object."))

        self.message("change style of selected objects:", verbosity=3)

        style = inkex.Style()

        if self.options.stroke_width < 0:
            style["stroke-width"] = self.config.get("laser_diameter", 0.2)
        else:
            style["stroke-width"] = self.options.stroke_width
        style["stroke-width"] = self.mm_to_svg(style["stroke-width"])

        if not self.options.stroke:
            style["stroke"] = "none"
        else:
            if self.options.stroke == "CUT_MODE":
                style["stroke"] = self.config.get("laser_mode_cut_color", "#ff0000")
            elif self.options.stroke == "FILL_MODE":
                style["stroke"] = self.config.get("laser_mode_fill_color", "#0000ff")
            elif self.options.stroke == "LINE_MODE":
                style["stroke"] = self.config.get("laser_mode_line_color", "#000000")
            else:
                style["stroke"] = self.options.stroke

        if not self.options.fill:
            style["fill"] = "none"
        else:
            style["fill"] = self.options.fill

        if not self.options.fill_opacity:
            style["fill-opacity"] = 1
        else:
            style["fill-opacity"] = self.options.fill_opacity / 100

        for s in self.options.extra_style.split(";"):
            s = s.strip()
            if not s:
                continue  # ignore empty options
            try:
                a, v = s.split(":")
                style[a] = v
            except TypeError:
                raise self.abort(
                    _("cannot parse extra style:"),
                    self.options.extra_style,
                )

        counter = 0
        for elem in self.selected_or_all(skip_groups=True):
            # skip non path elements (except if option only-paths is false)
            if self.options.only_paths:
                if not utils.is_path(elem):
                    continue

            msg_style = []
            for a in style:
                if elem.style.get(a) != style[a]:
                    msg_style.append(f"{a}:{style[a]}")
                    elem.style[a] = style[a]
            if msg_style:
                counter += 1
                self.message(
                    "\t-", f"object with id={elem.get_id()} modified with style:", ", ".join(msg_style), verbosity=2
                )

        self.message(f"the style of {counter} objects was modified", verbosity=1)
        self.message(
            _("{extension:s}: running time = {time:.0f}ms").format(extension=self.name, time=self.get_timer()),
            verbosity=3,
        )
        self.message("", verbosity=1)


if __name__ == "__main__":
    ChangeStyle().run()
