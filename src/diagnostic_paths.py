#!/usr/bin/env python

import re
import inkex

from lib import artefacts, utils
from lib.artefacts import OK, WARNING, ERROR


class MarkNonPaths(artefacts.Ext):
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

            # if we reach this point, the element should be a path / shape
            # we add an error and debug message in case I missed something
            if not utils.is_path(elem):
                self.outline_arrow(ERROR, elem, tr)
                self.msg("UNKWNOW: " + desc)

            # we now check for extra visible features that probably won't
            # translate automatically to path
            E = utils.effects(elem)

            if not E:
                # if elem is not a "strict" path but passed the is_path()
                # function, it must be a shape (rectangle, circle, etc.)
                if not utils.is_path(elem, strict=True) and self.options.outline_shapes:
                    self.outline_bounding_box(OK, elem, tr, msg=desc)
                continue

            # add list of effects to the description
            desc = desc + "\nEFFECTS: " + ", ".join(E)

            if E == ["path-effect"]:
                # path effects can be transformed to real path, so we only
                # give them a WARNING level)
                self.outline_bounding_box(WARNING, elem, tr, msg=desc)

            self.outline_bounding_box(ERROR, elem, tr, msg=desc)

        if clean:
            self.clean(force=False)


if __name__ == '__main__':
    MarkNonPaths().run()
