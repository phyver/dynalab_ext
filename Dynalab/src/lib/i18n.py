#!/usr/bin/env python

import gettext
import os

GETTEXT_DOMAIN = "dynalab"


class Ext:

    def __init__(self):
        super().__init__()

        # Set up gettext
        locale_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "locales"))
        domain = GETTEXT_DOMAIN
        gettext.bindtextdomain(domain, locale_dir)
        gettext.textdomain(domain)
