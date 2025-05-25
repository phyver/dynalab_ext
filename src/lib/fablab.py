#!/usr/bin/env python

import inkex
from lib import config, i18n, artefacts


# TODO: I should look for a list of valid tags, to check what I am missing!
# TODO: it might be better to use a white list of tags rather than a black list
def _skip(elem):
    """return true if the elem should be skipped as part of metadata"""
    return any((isinstance(elem, cls) for cls in
                [inkex.Defs, inkex.Desc, inkex.Metadata,
                 inkex.NamedView, inkex.Script, inkex.Style]))


def _iter_elements(
    elem,                       # current element
    recurse=True,               # should we recurse inside groups?
    skip_groups=False,          # should we return group elements?
    limit=None,                 # current limit for total number of returned elements
                                # if None, there is no limit; otherwise, limit should be a list with a single element
                                # that decreases each time we "yield" an element
    _global_transform=None,      # current transformation wrt root, accumulate transformation while going inside groups
):
    """recursively iterates over elements
    returns pairs consisting of an element together with its global
    transformation from the root of the document
    """
    _global_transform = _global_transform or inkex.transforms.Transform()
    if limit is not None and limit[0] <= 0:
        return

    # skip artefacts
    if artefacts.ARTEFACT_CLASS == elem.get("class"):
        return

    # skip non SVG elements
    if _skip(elem):
        return

    if not isinstance(elem, inkex.Group) or not skip_groups:
        yield elem, _global_transform
        if limit is not None:
            limit[0] -= 1

    # don't recurse in non-groups, or if recurse is False
    if not isinstance(elem, inkex.Group) or not recurse:
        return

    for e in elem:
        yield from _iter_elements(e,
                                  recurse=recurse,
                                  skip_groups=skip_groups,
                                  limit=limit,
                                  _global_transform=elem.transform @ _global_transform)


class Ext(artefacts.Ext, i18n.Ext, config.Ext):
    """main class for our extension with methods
      - to iterate over elements
      - to tag (either using arrows or bounding box boundaries) other elements
        by adding artefacts in a special "artefact layer"
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        i18n.Ext.__init__(self)
        config.Ext.__init__(self)

    def selected_or_all(self, recurse=False, skip_groups=False, limit=None):
        """iterates over the selected elements (recursively if needs be), or
        all the element if the selection is empty"""
        if limit is not None:
            limit = [limit]
        if not self.svg.selected:
            for elem in self.svg:
                yield from _iter_elements(elem,
                                          recurse=recurse,
                                          skip_groups=skip_groups,
                                          limit=limit)
        else:
            for elem in self.svg.selected:
                parent = elem.getparent()
                if parent is None:
                    # this can happen if the user selected an object in the
                    # error layer, which is removed before running a new
                    # extension
                    continue
                if not isinstance(elem, inkex.Group):
                    tr = parent.composed_transform()
                else:
                    tr = elem.composed_transform()
                yield from _iter_elements(elem, recurse=recurse,
                                          skip_groups=skip_groups,
                                          limit=limit,
                                          _global_transform=tr)
