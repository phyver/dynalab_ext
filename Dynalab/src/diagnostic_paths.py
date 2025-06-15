#!/usr/bin/env python

import inkex

from lib import dynalab, utils
from lib.dynalab import OK, WARNING, ERROR


class MarkNonPaths(dynalab.Ext):
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
                          default=True, help="outline simple shapes (rect, circles, etc.) that are not path",
                          dest="outline_shapes")
        pars.add_argument("--color-texts", type=inkex.Boolean,
                          default=False, help="use color to highlight text elements",
                          dest="color_texts")

    def effect(self, clean=True):
        self.message("looking for non path objects",
                     verbosity=3)
        self.init_artefact_layer()

        counter = [0, 0, 0, 0]
        for elem, tr in self.selected_or_all(skip_groups=True):

            desc = f"object with id={elem.get_id()} of type {elem.tag_name}"

            level = -1

            # root element, for recursively clone elements
            elem_ref = utils.get_clone_reference_element(elem)
            if isinstance(elem, inkex.Use):
                if elem_ref == elem.href:
                    desc += f" is a cloned version of id={elem.href.get_id()}, of type {elem.href.tag_name}"
                else:
                    desc += f" is a cloned version of id={elem.href.get_id()}, "
                    desc += f" with root element id={elem_ref.get_id()} of type {elem_ref.tag_name}"
                level = WARNING
            else:
                assert elem_ref == elem

            # warning for non vectorized texts
            if isinstance(elem_ref, inkex.TextElement):
                level = max(level, WARNING)
                desc += " is not vectorized"
                self.message("\t-", desc, verbosity=2)
                self.outline_bounding_box(level, elem, tr, msg=desc)
                continue

            # error around image
            if isinstance(elem_ref, inkex.Image):
                level = max(level, ERROR)
                desc += " is a non vectorized image"
                self.message("\t-", desc, verbosity=2)
                self.outline_bounding_box(level, elem, tr, msg=desc)
                continue

            # if we reach this point, the element should be a path / shape
            # we add an error and debug message in case I missed something
            if not utils.is_path(elem_ref):
                level = max(level, ERROR)
                desc += " is an unknown element! (Report this as a bug)"
                counter[ERROR] += 1
                self.message("\t-", desc, verbosity=2)
                self.outline_arrow(level, elem, tr)
                self.message("UNKNOWN ELEMENT:", desc)

            # we now check for extra visible features that probably won't
            # translate automatically to path
            E = utils.effects(elem_ref)

            if not E:
                # if elem is not a "strict" path but passed the is_path()
                # function, it must be a shape (rectangle, circle, etc.)
                if not utils.is_path(elem_ref, strict=True) and self.options.outline_shapes:
                    desc += " is a simple SVG shape"
                    level = max(level, OK)
                    counter[level] += 1
                    self.message("\t-", desc, verbosity=2)
                    self.outline_bounding_box(level, elem, tr, msg=desc)
                continue

            # add list of effects to the description
            desc += " with the following effects: " + ", ".join(E)
            self.message("\t-", desc, verbosity=2)

            if E == ["path-effect"]:
                # path effects can be transformed to real path, so we only
                # give them a WARNING level)
                level = max(level, WARNING)
                counter[level] += 1
                self.outline_bounding_box(level, elem, tr, msg=desc)
                continue

            level = max(level, ERROR)
            counter[level] += 1
            self.outline_bounding_box(level, elem, tr, msg=desc)

        if clean:
            self.clean(force=False)

        self.message(f"{sum(counter)} non-path object(s) have been found:",
                     verbosity=1)
        if counter[OK] > 0:
            self.message(f"\t- {counter[OK]} simple shape(s)",
                         verbosity=1)
        if counter[WARNING] > 0:
            self.message(f"\t- {counter[WARNING]} easily vectorizable object(s)",
                         verbosity=1)
        if counter[ERROR] > 0:
            self.message(f"\t- {counter[ERROR]} possibly problematic object(s)",
                         verbosity=1)

        self.message(f"looking for non path objects: running time = {self.running_time():.0f}ms",
                     verbosity=3)
        self.message("",
                     verbosity=1)


if __name__ == '__main__':
    MarkNonPaths().run()
