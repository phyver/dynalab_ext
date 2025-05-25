#!/usr/bin/env python

import re
import inkex

from lib import fablab


class MarkShapes(fablab.Ext):
    """
    mark shapes from the document:
      - path in green
      - standard shapes easily converted to path in orange
      - problematic shapes in red: text elements, clipped or masked shapes,
        shapes containing gradients, clones, images

    To avoid computing strange bounding boxes,
      - texts are copied in red to the error layer,
      - clones are simply pointed to by an arrow (they could be text)
    """

    def add_arguments(self, pars):
        pass

    def effect(self):
        self.init_error_layer()

        for elem, tr in self.selected_or_all(recurse=True,
                                             skip_groups=False,
                                             limit=None):

            tag = re.sub(r'^\{.*\}', '', elem.tag)
            desc = f"#{elem.get_id()} ({tag})"

            if isinstance(elem, inkex.Group):
                # ignore groups and layers (but recurse into them)
                continue

            # clone texts to the error layers, in red
            if isinstance(elem, inkex.TextElement):
                self.clone_text_to_error(elem, tr, msg=desc + " => not vectorized",
                                         stroke="#ff0000", stroke_width=".5mm", fill="#ff0000")
                self.new_error_arrow(elem, tr)
                continue

            # add red bounding box around image
            if isinstance(elem, inkex.Image):
                self.outline_bounding_box(elem, tr, msg=desc,
                                          stroke="#f00", stroke_width="1mm")
                continue

            # add red arrow pointing to use elements (clones)
            # because the element could be anything, including a text whose
            # bounding box is difficult to compute, we just use the arrow
            if isinstance(elem, inkex.Use):
                self.new_error_arrow(elem, tr, msg=desc + f" => cloned element {elem.get('xlink:href')}")
                continue

            # we check if the element is masked, clipped or filtered
            with_extra_feature = False
            if "mask" in elem.attrib:
                desc = "MASKED: " + desc
                with_extra_feature = True
            if "clip-path" in elem.attrib:
                desc = "CLIPPED: " + desc
                with_extra_feature = True
            if "filter" in elem.attrib:
                desc = "FILTERED: " + desc
                with_extra_feature = True

            # we now look if the element contains a gradient in the fill /
            # stroke attribute
            style = inkex.Style(elem.attrib.get("style", ''))
            fill1 = elem.attrib.get("fill")
            fill2 = style.get("fill")
            if fill1 and fill1.startswith("url(#") or fill2 and fill2.startswith("url(#"):
                desc = "GRADIENT FILLED: " + desc
                with_extra_feature = True
            stroke1 = elem.attrib.get("fill")
            stroke2 = style.get("stroke")
            if stroke1 and stroke1.startswith("url(#") or stroke2 and stroke2.startswith("url(#"):
                desc = "GRADIENT STROKED: " + desc
                with_extra_feature = True

            # if the element uses extra problematic features, add a red
            # bounding box
            # at this points, all elements should have well defined bounding
            # box
            if with_extra_feature:
                self.outline_bounding_box(elem, tr, stroke="#f00", stroke_width="1mm", msg=desc)
                continue

            # standard shapes that are not path should cause any problem, put
            # an orange bounding box
            if any((isinstance(elem, E) for E in [inkex.Line, inkex.Polyline, inkex.Polygon,
                                                  inkex.Rectangle, inkex.Ellipse, inkex.Circle])):
                self.outline_bounding_box(elem, tr, stroke=inkex.Color("orange"), stroke_width="0.3mm", msg=desc)

            # the final case: put a green bounding box around standard path
            # elements
            elif isinstance(elem, inkex.PathElement):
                self.outline_bounding_box(elem, tr, stroke="#0f0", stroke_width="0.3mm", msg=desc)

            else:   # just in case I missed something
                self.msg("UNKWNOW: " + desc)


if __name__ == '__main__':
    MarkShapes().run()
