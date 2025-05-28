#!/usr/bin/env python

import inkex

from lib import artefacts


class Ungroups(artefacts.Ext):
    """
    constantly changing dummy extension to test features for upcoming
    extensions
    Can serve as a basis for new extensions.
    """

    def add_arguments(self, pars):
        pass

    def effect(self):
        # find all groups / layers in the selection
        groups = []
        for elem, tr in self.selected_or_all(recurse=True,
                                             skip_groups=False,
                                             limit=None):
            if isinstance(elem, inkex.Group):
                groups.append((elem, tr))

        # reverse the order, so that deeper groups are removed first
        groups.reverse()
        for gr, tr in groups:
            if gr.attrib.get("clip-path", "none") != "none":
                self.msg(f"""WARNING: group {gr.get('id')} contains a clip-path
which is discarded. If that is a problem, Undo (Ctrl-z) the ungrouping and
find a way to deal with that. (The "Arrange" => "deep-ungroup" extension might
be a solution.)""")
            for elem in gr:
                gr.remove(elem)
                elem.transform = tr @ gr.transform @ elem.transform
                self.svg.add(elem)
            gr.getparent().remove(gr)


if __name__ == '__main__':
    Ungroups().run()
