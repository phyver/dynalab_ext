#!/usr/bin/env python

from gettext import gettext as _
from gettext import ngettext

import inkex

from lib import dynalab
from lib.dynalab import NOTE
from lib.intervaltree import IntervalTree


def compute_blobs(BB):
    tree = IntervalTree()
    # Add each box to the interval tree by x-interval
    for id, bb in BB:
        simplified = False  # because bb can get bigger, we need to keep looking for boxes that intersect it
        ids = [id]
        while not simplified:
            simplified = True
            # Find all boxes whose x-interval overlaps the current x-interval
            candidates = tree[bb.left : bb.right]
            for itv in candidates:
                ids2, bb2 = itv.data
                if bb & bb2:
                    simplified = False
                    bb = bb + bb2
                    ids.extend(ids2)
                    tree.remove(itv)
        tree.addi(bb.left, bb.right, (ids, bb))
    return [itv.data for itv in tree]


class MarkBlobs(dynalab.Ext):
    """
    aggregate bounding boxes into blobs and mark disconnected blobs
    """

    name = _("mark blobs")

    def add_arguments(self, pars):
        pars.add_argument("--padding", type=float, default=10, help="padding added to boxes to check overlap (mm)")

    def effect(self, clean=True):
        self.message(self.name, verbosity=3)
        self.init_artifact_layer()

        BB = []
        for elem in self.selected_or_all(skip_groups=True):
            BB.append((elem.get_id(), self.bounding_box(elem)))

        # add padding around bbs
        padding = self.mm_to_svg(self.options.padding)
        for i, (id, bb) in enumerate(BB):
            x, y, w, h = bb.left, bb.top, bb.width, bb.height
            BB[i] = id, inkex.BoundingBox.new_xywh(x - padding, y - padding, w + 2 * padding, h + 2 * padding)

        BBB = compute_blobs(BB)

        # don't mark anything if there is only one blob
        if len(BBB) > 1:
            for ids, bbb in BBB:
                desc = _("the following object(s) form an isolated blob:")
                desc += " " + ", ".join(ids)
                self.outline_bounding_box(NOTE, None, bb=bbb, margin=0, msg=desc)

        if clean:
            self.clean_artifacts(force=False)

        counter = len(BBB)
        self.message(
            ngettext("{counter} bounding boxes blob found", "{counter} bounding boxes blobs found", counter).format(
                counter=counter
            ),
            verbosity=1,
        )
        self.message(
            _("{extension:s}: running time = {time:.0f}ms").format(extension=self.name, time=self.get_timer()),
            verbosity=3,
        )
        self.message("", verbosity=1)


if __name__ == "__main__":
    MarkBlobs().run()
