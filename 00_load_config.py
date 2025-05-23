#!/usr/bin/env python
# coding=utf-8

import inkex
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "current_config.json")


class LoadConfig(inkex.EffectExtension):

    def add_arguments(self, pars):
        default_path = os.path.dirname(os.path.realpath(__file__))
        pars.add_argument("--config-file", default=default_path, help="Load file", dest="config_file")

    def effect(self):
        pass
        # TODO error if file doesn't exist
        # TODO try to load the file
        # TODO: copy config_file to CONFIG_FILE


if __name__ == '__main__':
    LoadConfig().run()
