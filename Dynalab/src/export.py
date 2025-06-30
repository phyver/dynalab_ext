#!/usr/bin/env python

import re
import os
import sys
import time

import inkex

from lib import dynalab


class Export(dynalab.Ext):
    """
    constantly changing dummy extension to test features for upcoming
    extensions
    Can serve as a basis for new extensions.
    """

    def add_arguments(self, pars):
        pars.add_argument("--clean", type=inkex.Boolean, default=True, help="remove artifacts")
        pars.add_argument("--svg", type=inkex.Boolean, default=False, help="save to svg")
        pars.add_argument("--dxf", type=inkex.Boolean, default=True, help="export to dxf")
        pars.add_argument("--pdf", type=inkex.Boolean, default=True, help="export to pdf")

        pars.add_argument("--filename", type=str, default="", help="filename (no extension)")
        pars.add_argument("--savedir", type=str, default="", help="save directory")

    def effect(self):

        if not any([self.options.dxf, self.options.pdf, self.options.svg]):
            self.abort("", "nothing to do: you must select at least one export format")

        if not self.options.savedir:
            self.abort("", "empty savedir")

        if not os.path.isdir(self.options.savedir):
            self.abort("", f"{self.options.savedir} isn't a directory")
        if not os.access(self.options.savedir, os.R_OK | os.W_OK):
            self.abort("", f"not enough permissions to write to {self.options.savedir}")

        if not self.options.filename:
            self.options.filename = self.svg.attrib.get('sodipodi:docname') or ""

        # remove extension
        self.options.filename = re.sub(r"\.*?$", "", self.options.filename)

        if not self.options.filename:
            self.abort("", "empty filename")

        if not re.match("[-_a-zA-Z0-9]*", self.options.filename):
            self.abort("",
                       "invalid filename, use only ASCII letters and digits (A-Z, a-z, 0-9),",
                       "underscore (_) and minus sign (-)",
                       sep="\n",
                       )

        savefile = os.path.join(self.options.savedir, self.options.filename)

        self.message(f"exporting svg document to {savefile}",
                     "(with additional extension)",
                     verbosity=1)

        if self.options.clean:
            self.clean_artifacts(force=True)

        counter = 0
        if self.options.pdf:
            counter += 1
            self.message("\t-", f"saving to svg: {savefile+'.svg'}",
                         verbosity=1)
            start_time = time.perf_counter()
            self.export_with_inkscape(savefile+".svg", "svg")
            self.message("\t\t", f"running time {1000*(time.perf_counter()-start_time):.0f}ms",
                         verbosity=3)

        if self.options.dxf:
            # NOTE: exporting to dxf defaults to dxf12, so I have to
            # explicitly give the extension id
            # NOTE: by default, exporting to dxf14 uses "unit_from_document"
            # so there shouldn't be any need to specify "units:mm"
            # which is great because I don't know how to do that.
            counter += 1
            self.message("\t-", f"exporting to dxf14: {savefile+'.dxf'}",
                         verbosity=1)
            start_time = time.perf_counter()
            self.export_with_inkscape(savefile+".dxf", "dxf",
                                      "--export-extension=org.ekips.output.dxf_outlines",
                                      )
            self.message("\t\t", f"running time {1000*(time.perf_counter()-start_time):.0f}ms",
                         verbosity=3)

        if self.options.pdf:
            counter += 1
            self.message("\t-", f"exporting to pdf: {savefile+'.pdf'}",
                         verbosity=1)
            start_time = time.perf_counter()
            self.export_with_inkscape(savefile+".pdf", "pdf")
            self.message("\t\t", f"running time {1000*(time.perf_counter()-start_time):.0f}ms",
                         verbosity=3)

        self.message(f"{counter} document(s) exported")
        self.message(f"total running time = {self.running_time():.0f}ms",
                     verbosity=3)
        self.message("",
                     verbosity=1)

    def export_with_inkscape(self, savefile, export_format, *args):
        if not self.options.input_file:
            self.abort("save your project first")

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


if __name__ == '__main__':
    Export().run()
