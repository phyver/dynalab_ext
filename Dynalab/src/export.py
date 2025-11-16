#!/usr/bin/env python

import os
import re
import sys
from gettext import gettext as _
from gettext import ngettext

import inkex

from lib import dynalab


class Export(dynalab.Ext):
    """
    export SVG document to different formats
    """

    name = _("export document")

    def add_arguments(self, pars):
        pars.add_argument("--clean", type=inkex.Boolean, default=True, help="remove artifacts")
        pars.add_argument("--svg", type=inkex.Boolean, default=False, help="save to svg")
        pars.add_argument("--dxf", type=inkex.Boolean, default=True, help="export to dxf")
        pars.add_argument("--pdf", type=inkex.Boolean, default=True, help="export to pdf")

        pars.add_argument("--filename", type=str, default="", help="filename (no extension)")
        pars.add_argument("--savedir", type=str, default="", help="save directory")

    def effect(self):

        if not any([self.options.dxf, self.options.pdf, self.options.svg]):
            self.abort("", _("nothing to do: you must select at least one export format"))

        if not self.options.savedir:
            self.abort("", _("no savedir given"))

        if not os.path.isdir(self.options.savedir):
            self.abort("", _("{savedir} isn't a directory").format(savedir=self.options.savedir))
        if not os.access(self.options.savedir, os.R_OK | os.W_OK):
            self.abort("", _("not enough permissions to write to {savedir}").format(savedir=self.options.savedir))

        if not self.options.filename:
            self.options.filename = self.svg.attrib.get("sodipodi:docname") or ""

        # remove extension
        self.options.filename = re.sub(r"\.*?$", "", self.options.filename)

        if not self.options.filename:
            self.abort("", _("filename not given"))

        if not re.match("[-_a-zA-Z0-9]*", self.options.filename):
            self.abort(
                "",
                _(
                    """invalid filename, use only ASCII letters and digits (A-Z, a-z, 0-9),
"underscore" (_) and minus sign (-)"""
                ),
                sep="\n",
            )

        savefile = os.path.join(self.options.savedir, self.options.filename)

        self.message(
            _("exporting SVG document to {savefile} (with additional extension)").format(savefile=savefile), verbosity=1
        )

        if self.options.clean:
            self.clean_artifacts(force=True)

        counter = 0
        if self.options.svg:
            counter += 1
            self.message("\t-", _("exporting to {format}").format(format="SVG") + ": " + savefile + ".svg", verbosity=1)
            self.set_timer("export_svg")
            self.export_with_inkscape(savefile + ".svg", "svg")
            self.message(
                "\t\t",
                _("{extension:s}: running time = {time:.0f}ms").format(
                    extension=_("exporting to {format}").format(format="SVG"), time=self.get_timer("export_svg")
                ),
                verbosity=3,
            )

        if self.options.dxf:
            # NOTE: exporting to dxf defaults to dxf12, so I have to
            # explicitly give the extension id
            # NOTE: by default, exporting to dxf14 uses "unit_from_document"
            # so there shouldn't be any need to specify "units:mm"
            # which is great because I don't know how to do that.
            counter += 1
            self.message(
                "\t-", _("exporting to {format}").format(format="DXF14") + ": " + savefile + ".dxf", verbosity=1
            )
            self.set_timer("export_dxf")
            self.export_with_inkscape(
                savefile + ".dxf",
                "dxf",
                "--export-extension=org.ekips.output.dxf_outlines",
            )
            self.message(
                "\t\t",
                _("{extension:s}: running time = {time:.0f}ms").format(
                    extension=_("exporting to {format}").format(format="DXF14"), time=self.get_timer("export_dxf")
                ),
                verbosity=3,
            )

        if self.options.pdf:
            counter += 1
            self.message("\t-", _("exporting to {format}").format(format="PDF") + ": " + savefile + ".pdf", verbosity=1)
            self.set_timer("export_pdf")
            self.export_with_inkscape(savefile + ".pdf", "pdf")
            self.message(
                "\t\t",
                _("{extension:s}: running time = {time:.0f}ms").format(
                    extension=_("exporting to {format}").format(format="PDF"), time=self.get_timer("export_dxf")
                ),
                verbosity=3,
            )

        self.message(
            ngettext("{counter} document exported", "{counter} documents exported", counter).format(counter=counter)
        )
        self.message(
            _("{extension:s}: running time = {time:.0f}ms").format(extension=self.name, time=self.get_timer()),
            verbosity=3,
        )
        self.message("", verbosity=1)

    def export_with_inkscape(self, savefile, export_format, *args):
        if not self.options.input_file:
            self.abort(_("You must save your project."))

        try:
            inkex.command.inkscape(
                self.options.input_file,
                f"--export-filename={savefile}",
                f"--export-type={export_format}",
                *args,
            )
        except inkex.command.ProgramRunError as e:
            self.abort(
                f"external inkscape command failed with error code {e.returncode}",
                "command: " + " ".join(e.arguments),
                "stdout:\n" + e.stdout.decode(sys.stdout.encoding or "UTF-8") if e.stdout else None,
                "stderr:\n" + e.stderr.decode(sys.stderr.encoding or "UTF-8") if e.stderr else None,
                sep="\n",
            )


if __name__ == "__main__":
    Export().run()
