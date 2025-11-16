#!/usr/bin/env python

from gettext import gettext as _
from gettext import ngettext

from lib import dynalab
from lib.dynalab import ERROR


class MarkTiny(dynalab.Ext):
    """
    mark the "tiny" elements found in the document
    """

    name = _("mark tiny objects")

    def add_arguments(self, pars):
        pars.add_argument(
            "--size-tiny-element", type=float, dest="size_tiny_element", help="size for tiny elements (mm)"
        )

    def effect(self, clean=True):
        self.message(self.name, verbosity=3)
        self.init_artifact_layer()
        tiny = self.options.size_tiny_element or self.config["size_tiny_element"]

        counter = 0
        for elem in self.selected_or_all(skip_groups=True):
            desc = _("object with id={id} of type {tag}").format(id=elem.get_id(), tag=elem.tag_name)
            bb = self.bounding_box(elem)
            if self.svg_to_mm(bb.width) < tiny and self.svg_to_mm(bb.height) < tiny:
                desc += " " + _("is 'tiny'")
                counter += 1
                self.message("\t-", desc, verbosity=2)
                self.outline_bounding_box(ERROR, elem, msg=desc)

        if clean:
            self.clean_artifacts(force=False)

        self.message(
            ngettext("{counter} tiny object found", "{counter} tiny objects found", counter).format(counter=counter),
            verbosity=1,
        )
        self.message(
            _("{extension:s}: running time = {time:.0f}ms").format(extension=self.name, time=self.get_timer()),
            verbosity=3,
        )
        self.message("", verbosity=1)


if __name__ == "__main__":
    MarkTiny().run()
