#!/usr/bin/env python

from lib.intervaltree import IntervalTree

import inkex

from lib import dynalab, utils
from lib.dynalab import NOTE


def compute_blobs(BB):
    tree = IntervalTree()
    # Add each box to the interval tree by x-interval
    for id, bb in BB:
        simplified = False      # because bb can get bigger, we need to keep looking for boxes that intersect it
        ids = [id]
        while not simplified:
            simplified = True
            # Find all boxes whose x-interval overlaps the current x-interval
            candidates = tree[bb.left:bb.right]
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

    def add_arguments(self, pars):
        pars.add_argument("--padding", type=float, default=10, help="padding added to boxes to check overlap (mm)")

    def effect(self, clean=True):
        self.message("looking for bounding boxes blobs",
                     verbosity=3)
        self.init_artifact_layer()

        BB = []
        for elem in self.selected_or_all(skip_groups=True):
            BB.append((elem.get_id(),
                       self.bounding_box(elem)))

        # add padding around bbs
        padding = self.mm_to_svg(self.options.padding)
        for i, (id, bb) in enumerate(BB):
            x, y, w, h = bb.left, bb.top, bb.width, bb.height
            BB[i] = id, inkex.BoundingBox.new_xywh(x-padding, y-padding,
                                                   w+2*padding, h+2*padding)

        BBB = compute_blobs(BB)

        # don't mark anything if there is only one blob
        if len(BBB) > 1:
            for ids, bbb in BBB:
                desc = "the following objects form an isolated blob: "
                desc += ", ".join(ids)
                self.outline_bounding_box(NOTE, None, bb=bbb, margin=0,
                                          msg=desc)

        if clean:
            self.clean_artifacts(force=False)

        self.message(f"{len(BBB)} bounding boxes blob(s) found",
                     verbosity=1)
        self.message(f"looking for bounding boxes blobs: running time = {self.running_time():.0f}ms",
                     verbosity=3)
        self.message("",
                     verbosity=1)


if __name__ == '__main__':
    MarkBlobs().run()
