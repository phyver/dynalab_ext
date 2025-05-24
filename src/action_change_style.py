#!/usr/bin/env python

from gettext import gettext as _
import inkex

from lib import fablab


class ChangeStyle(fablab.Ext):
    """
    apply some new style (stroke-width, color and fill-color) to the selection
    """
    # TODO: I could store a dictionary self.new_style and pass arbitrary style
    # attributes.

    def __init__(self, mode="line", color=None, fill=None, width=None):
        """if specific attributes are not given, color is taken from the
        current configuration mode-color, as is stroke-width (laser diameter);
        fill is set to "none".
        """
        super().__init__()
        self.new_color = color or self.config.get(f"laser_mode_{mode}_color")
        self.new_fill = fill or "none"
        self.new_width = width or self.config.get("misc_laser_diameter")

    def add_arguments(self, pars):
        pass    # We don't need arguments for this extension

    def effect(self):
        if not self.svg.selected:
            raise inkex.AbortExtension("\n\n" + _("YOU MUST SELECT AT LEAST ONE ELEMENT") + "\n\n")
        self.init_error_layer()

        # TODO should I apply to all elements if the selection is empty?
        # TODO should I tag text blocks
        for elem, tr in self.selected_or_all(recurse=True,
                                             skip_groups=True,
                                             limit=None):
            if self.new_color:
                elem.style["stroke"] = self.new_color
            if self.new_width:
                elem.style["stroke-width"] = self.new_width
            if self.new_fill:
                elem.style["fill"] = self.new_fill
