#!/usr/bin/env python

from gettext import gettext as _

from lib import dynalab


class About(dynalab.Ext):

    def add_arguments(self, pars):
        pass

    def effect(self):
        try:
            import version

            version_tag = version.tag

        except ModuleNotFoundError:
            version_tag = "unkwnown developpment version"

        self.message(
            _(
                """
Dynalab is a set of Inkscape extensions used to assist beginners in
preparing documents before sending them to appropriate software on a
laser cutter / laser engraver.

This is version "{version_tag:s}"

More information about Dynalab can be found at
    TODO
"""
            ).format(version_tag=version_tag)
        )


if __name__ == "__main__":
    About().run()
