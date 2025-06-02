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
                          default=False, help="outline simple shapes (rect, circles, etc.) that are not path",
                          dest="outline_shapes")
        pars.add_argument("--color-texts", type=inkex.Boolean,
                          default=False, help="use color to highlight text elements",
                          dest="color_texts")

    def effect(self, clean=True):
        self.message("looking for non path objects",
                     verbosity=3)
        self.init_artefact_layer()

        missing_bbs = []

        counter = [0, 0, 0, 0]
        for elem, tr in self.selected_or_all(recurse=True,
                                             skip_groups=False,
                                             limit=None):

            desc = f"object with id={elem.get_id()} of type {elem.tag_name}"

            if isinstance(elem, inkex.Group):
                # ignore groups and layers (but recurse into them)
                continue

            # mark non vectorized texts
            if isinstance(elem, inkex.TextElement):
                desc += " is not vectorized"
                self.message("\t-", desc, verbosity=2)
                if self.options.color_texts:
                    # clone texts to the error layers, in red
                    self.outline_text(WARNING, elem, tr, msg=desc)
                else:
                    # use inkscape to compute bounding boxes in bulk
                    missing_bbs.append((elem, desc))
                continue

            # add red bounding box around image
            if isinstance(elem, inkex.Image):
                counter[ERROR] += 1
                desc += " is possibly a non vectorized image"
                self.message("\t-", desc, verbosity=2)
                self.outline_bounding_box(ERROR, elem, tr, msg=desc)
                continue

            if isinstance(elem, inkex.Use):
                # root element, for recursively clone elements
                ref = utils.get_clone_reference_element(elem)
                if ref == elem.href:
                    desc += f" is a cloned version of id={elem.href.get_id()}, of type {elem.href.tag_name}"
                else:
                    desc += f" is a cloned version of id={elem.href.get_id()}, "
                    desc += f" with root element id={ref.get_id()} of type {ref.tag_name}"
                self.message("\t-", desc, verbosity=2)
                # use inkscape to compute bounding boxes in bulk
                missing_bbs.append((elem, desc))
                continue

            # if we reach this point, the element should be a path / shape
            # we add an error and debug message in case I missed something
            if not utils.is_path(elem):
                desc += " is an unknown element! (Report this as a bug)"
                counter[ERROR] += 1
                self.message("\t-", desc, verbosity=2)
                self.outline_arrow(ERROR, elem, tr)
                self.message("UNKWNOW ELEMENT:", desc)

            # we now check for extra visible features that probably won't
            # translate automatically to path
            E = utils.effects(elem)

            if not E:
                # if elem is not a "strict" path but passed the is_path()
                # function, it must be a shape (rectangle, circle, etc.)
                if not utils.is_path(elem, strict=True) and self.options.outline_shapes:
                    desc += " is a simple SVG shape, you can probably leave it"
                    counter[OK] += 1
                    self.message("\t-", desc, verbosity=2)
                    self.outline_bounding_box(OK, elem, tr, msg=desc)
                continue

            # add list of effects to the description
            desc += " with the following effects: " + ", ".join(E)
            self.message("\t-", desc, verbosity=2)

            if E == ["path-effect"]:
                # path effects can be transformed to real path, so we only
                # give them a WARNING level)
                counter[WARNING] += 1
                self.outline_bounding_box(WARNING, elem, tr, msg=desc)
                continue

            counter[ERROR] += 1
            self.outline_bounding_box(ERROR, elem, tr, msg=desc)

        if missing_bbs:
            elems, descs = zip(*missing_bbs)
            bbs = self.get_inkscape_bboxes(*elems)
            for elem, bb, desc in zip(elems, bbs, descs):
                ref = utils.get_clone_reference_element(elem)
                elem = ref
                if isinstance(elem, inkex.TextElement):
                    level = WARNING
                elif isinstance(elem, inkex.Image):
                    level = ERROR
                elif not utils.is_path(elem):
                    # unkwnown element! Should I add this to the description /
                    # message?
                    level = ERROR
                else:
                    E = utils.effects(elem)
                    if not E or E == ["path-effect"]:
                        level = WARNING
                    else:
                        level = ERROR
                counter[level] += 1
                self.draw_bounding_box(level, bb, msg=desc)

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
