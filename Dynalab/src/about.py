#!/usr/bin/env python

from lib import dynalab


class About(dynalab.Ext):

    def add_arguments(self, pars):
        pass

    def effect(self):
        try:
            import version
            v = version.tag

        except ModuleNotFoundError:
            v = "unkwnown developpment version"

        self.message(f"""

Dynalab is a set of Inkscape extensions used to assist beginners in
preparing documents before sending them to appropriate software on a
laser engraver.

This is version "{v}"

More information about Dynalab can be found at
    TODO

""")


if __name__ == '__main__':
    About().run()
