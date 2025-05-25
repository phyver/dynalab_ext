#!/usr/bin/env python

import re
from gettext import gettext as _
import inkex

from lib import fablab

# inkex.Group
# inkex.Layer (instance of inkex.Group)

# inkex.TextElement
# can contain an inkex.TextPath referencing a path

# inkex.Ellipse
# inkex.Circle
# inkex.Rectangle

# inkex.PathElement
# inkex.Line        NOTE: inkscape uses PathElement instead
# inkex.Polyline    NOTE: inkscape uses PathElement instead
# inkex.Polygon     NOTE: inkscape uses PathElement instead
#
# inkex.Image
# inkex.Use / inkex.Symb
#
# ???
# inkex.ClipPath




class MiscTests(fablab.Ext):
    """
    constantly changing dummy extension to test features for upcoming
    extensions
    Can serve as a basis for new extensions.
    """

    def add_arguments(self, pars):
        pass

    def effect(self):
        self.init_error_layer()

        for elem, tr in self.selected_or_all(recurse=True,
                                             skip_groups=False,
                                             limit=None):

            tag = re.sub(r'^\{.*\}', '', elem.tag)
            desc = f"{tag} => #{elem.get_id()}"

            if isinstance(elem, inkex.Layer):
                self.msg(f"Layer => {desc}")
                continue

            if isinstance(elem, inkex.Group):
                self.outline_bounding_box(elem, tr, stroke="#aaa", stroke_width="1mm", msg=desc)
                continue

            if isinstance(elem, inkex.TextElement):
                self.new_error_arrow(elem, tr, msg=desc)
                continue
            elif isinstance(elem, inkex.Use) or isinstance(elem, inkex.Image):
                self.outline_bounding_box(elem, tr, stroke="#f00", stroke_width="1mm", msg=desc)
                continue

            with_attribute = False
            if "mask" in elem.attrib:
                desc = "MASKED: " + desc
                with_attribute = True
            if "clip-path" in elem.attrib:
                desc = "CLIPPED: " + desc
                with_attribute = True
            if "filter" in elem.attrib:
                desc = "FILTERED: " + desc
                with_attribute = True
            style = inkex.Style(elem.attrib.get("style", ''))
            fill1 = elem.attrib.get("fill")
            fill2 = style.get("fill")
            if fill1 and fill1.startswith("url(#") or fill2 and fill2.startswith("url(#"):
                desc = "GRADIENT FILLED: " + desc
                with_attribute = True
            stroke1 = elem.attrib.get("fill")
            stroke2 = style.get("stroke")
            if stroke1 and stroke1.startswith("url(#") or stroke2 and stroke2.startswith("url(#"):
                desc = "GRADIENT STROKED: " + desc
                with_attribute = True

            if with_attribute:
                self.outline_bounding_box(elem, tr, stroke="#f00", stroke_width="1mm", msg=desc)
                continue

            if isinstance(elem, inkex.Line) or isinstance(elem, inkex.Polyline) or isinstance(elem, inkex.Polygon) or isinstance(elem, inkex.Rectangle) or isinstance(elem, inkex.Ellipse) or isinstance(elem, inkex.Circle):
                self.outline_bounding_box(elem, tr, stroke=inkex.Color("orange"), stroke_width="0.3mm", msg=desc)

            elif isinstance(elem, inkex.PathElement):
                self.outline_bounding_box(elem, tr, stroke="#0f0", stroke_width="0.3mm", msg=desc)

            else:
                self.msg("UNKWNOW: " + desc)


            # r = random.randrange(0, 1)
            # if r == 0:
            #     self.new_error_arrow(elem, tr, msg=desc)
            # elif r == 1:
            #     self.new_warning_arrow(elem, tr, msg=desc)
            # elif r == 2:
            #     self.new_note_arrow(elem, tr, msg=desc)
            # elif r == 3:
            #     self.outline_bounding_box(elem, tr, color="#f00", msg=desc)
            # elif r == 4:
            #     self.outline_bounding_box(elem, tr,
            #                               color=inkex.Color("orange"),
            #                               msg=desc)
            # elif r == 5:
            #     self.outline_bounding_box(elem, tr, color="#0f0", msg=desc)


if __name__ == '__main__':
    MiscTests().run()
