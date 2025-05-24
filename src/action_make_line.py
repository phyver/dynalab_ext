#!/usr/bin/env python

from action_change_style import ChangeStyle

"""
change all the selected elements to "line" mode
(color and stroke width are taken from the current configuration)
"""

if __name__ == '__main__':
    ChangeStyle(mode="line").run()
