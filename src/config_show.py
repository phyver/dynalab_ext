#!/usr/bin/env python
# coding=utf-8

from lib import config


class ShowConfig(config.ConfigExt):

    def add_arguments(self, pars):
        pass

    def effect(self):
        self.show_config()


if __name__ == '__main__':
    ShowConfig().run()
