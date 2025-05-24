#!/usr/bin/env python

from gettext import gettext as _
import inkex

from lib import fablab

import random


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

        # randomly mark the selected elements
        for elem, tr in self.selected_or_all(recurse=True,
                                             skip_groups=True,
                                             limit=None):
            desc = elem.get_id()
            r = random.randrange(0, 6)
            if r == 0:
                self.new_error_arrow(elem, tr, msg=desc)
            elif r == 1:
                self.new_warning_arrow(elem, tr, msg=desc)
            elif r == 2:
                self.new_note_arrow(elem, tr, msg=desc)
            elif r == 3:
                self.outline_bounding_box(elem, tr, color="#f00", msg=_("lorem"))
            elif r == 4:
                self.outline_bounding_box(elem, tr,
                                          color=inkex.Color("orange"),
                                          msg=_("lorem"))
            elif r == 5:
                self.outline_bounding_box(elem, tr, color="#0f0", msg=_("lorem"))


if __name__ == '__main__':
    MiscTests().run()
