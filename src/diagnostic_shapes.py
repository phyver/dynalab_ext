#!/usr/bin/env python

import re
import inkex

from lib import artefacts
from lib.artefacts import OK, WARNING, ERROR


class MarkShapes(artefacts.Ext):
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
        pars.add_argument("--outline-shapes", type=inkex.Boolean,
                          default=False, help="outline simple shapes (rect, circles, etc.) that are not path",
                          dest="outline_shapes")
        pars.add_argument("--color-texts", type=inkex.Boolean,
                          default=True, help="use color to highlight text elements(faster)",
                          dest="color_texts")

    def effect(self, clean=True):
        self.init_artefact_layer()

        for elem, tr in self.selected_or_all(recurse=True,
                                             skip_groups=False,
                                             limit=None):

            tag = re.sub(r'^\{.*\}', '', elem.tag)
            desc = f"#{elem.get_id()} ({tag})"

            if isinstance(elem, inkex.Group):
                # ignore groups and layers (but recurse into them)
                continue

            # mark non vectorized texts
            if isinstance(elem, inkex.TextElement):
                if self.options.color_texts:
                    # clone texts to the error layers, in red
                    self.outline_text(WARNING, elem, tr, msg=desc + " => not vectorized")
                    self.outline_arrow(WARNING, elem, tr)
                else:
                    # use the slow (accept_text=True) outline method
                    self.outline_bounding_box(WARNING, elem, tr, msg=desc + " => not vectorized",
                                              accept_text=True)

                continue

            # add red bounding box around image
            if isinstance(elem, inkex.Image):
                self.outline_bounding_box(ERROR, elem, tr, msg=desc)
                continue

            # add orange arrow pointing to use elements (clones)
            # because the element could be anything, including a text whose
            # bounding box is difficult to compute, we just use the arrow
            if isinstance(elem, inkex.Use):
                self.outline_arrow(WARNING, elem, tr, msg=desc + f" => cloned element {elem.get('xlink:href')}")
                continue

            # we check for path effects (those can be transformed to real
            # path, so we only give them a WARNING level)
            extra_feature_level = -1
            if elem.get("inkscape:path-effect") is not None:
                desc = "PATH-EFFECT: " + desc
                extra_feature_level = max(extra_feature_level, WARNING)

            # we check if the element is masked, clipped or filtered
            if elem.attrib.get("mask", "none") != "none":
                desc = "MASKED: " + desc
                extra_feature_level = max(extra_feature_level, ERROR)
            if elem.attrib.get("clip-path", "none") != "none":
                desc = "CLIPPED: " + desc
                extra_feature_level = max(extra_feature_level, ERROR)
            if elem.attrib.get("filter", "none") != "none":
                desc = "FILTERED: " + desc
                extra_feature_level = max(extra_feature_level, ERROR)

            # we now look if the element contains a gradient in the fill /
            # stroke attribute
            style = inkex.Style(elem.attrib.get("style", ''))
            fill1 = elem.attrib.get("fill")
            fill2 = style.get("fill")
            if fill1 and fill1.startswith("url(#") or fill2 and fill2.startswith("url(#"):
                desc = "GRADIENT or PATTERN FILLED: " + desc
                extra_feature_level = max(extra_feature_level, ERROR)
            stroke1 = elem.attrib.get("fill")
            stroke2 = style.get("stroke")
            if stroke1 and stroke1.startswith("url(#") or stroke2 and stroke2.startswith("url(#"):
                desc = "GRADIENT STROKED: " + desc
                extra_feature_level = max(extra_feature_level, ERROR)

            # if the element uses extra problematic features, add a red
            # bounding box
            # at this points, all elements should have well defined bounding
            # box
            if extra_feature_level > 0:
                self.outline_bounding_box(extra_feature_level, elem, tr, msg=desc)
                continue

            # standard shapes that are not path should not cause any problem
            if any((isinstance(elem, E) for E in [inkex.Line, inkex.Polyline, inkex.Polygon,
                                                  inkex.Rectangle, inkex.Ellipse, inkex.Circle])):
                if self.options.outline_shapes:
                    self.outline_bounding_box(OK, elem, tr, msg=desc)
                continue

            # standard path elements: do nothing
            if isinstance(elem, inkex.PathElement):
                continue

            # just in case I missed something
            self.msg("UNKWNOW: " + desc)

        if clean:
            self.clean(force=False)


if __name__ == '__main__':
    MarkShapes().run()
