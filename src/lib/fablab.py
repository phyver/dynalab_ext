#!/usr/bin/env python

import inkex
from lib import config, i18n
from inkex.paths import Move, Line


# TODO: I should look for a list of valid tags, to check what I am missing!
# TODO: it might be better to use a white list of tags rather than a black list
skip_tags = {
    inkex.addNS('defs', 'svg'),
    inkex.addNS('desc', 'svg'),
    inkex.addNS('metadata', 'svg'),
    inkex.addNS('namedview', 'sodipodi'),
    inkex.addNS('script', 'svg'),
    inkex.addNS('style', 'svg'),
}


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

    # skip error layer
    if elem.get("id") == "ErrorLayer":
        return

    # skip non SVG elements
    if elem.tag in skip_tags:
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
                                  _global_transform=_global_transform @ elem.transform)


class Ext(i18n.Ext, config.Ext):
    """main class for our extension with methods
      - to iterate over elements
      - to tag (either using arrows or bounding box boundaries) other elements
        by adding artefacts in a special "error layer"
    """

    def __init__(self):
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

    def init_misc(self):
        # make sure the unit is "mm"
        self.svg.namedview.set(inkex.addNS('document-units', 'inkscape'), 'mm')

    def init_error_layer(self):
        """create a special error layer to put all errors / warning artefacts
        Artefacts are put inside a group in this layer for easy removal.
        If either the group or the layer already exists, it is cleared first.
        """
        self.init_misc()

        root = self.document.getroot()

        error_layer = self.svg.getElementById("ErrorLayer")
        error_group = self.svg.getElementById("ErrorGroup")

        if error_group is not None:
            error_group.clear()
            error_group.getparent().remove(error_group)

        if error_layer is not None:
            error_layer.clear()
            error_layer.getparent().remove(error_layer)

        # Create a new layer (group with groupmode 'layer')
        error_layer = inkex.Layer.new('ErrorLayer')
        error_layer.set("id", "ErrorLayer")
        # error_layer.set_sensitive(False)
        root.add(error_layer)

        # and create Inkscape group inside
        self.error_group = inkex.Group()
        self.error_group.set("id", "ErrorGroup")
        error_layer.add(self.error_group)

        # define the arrow markers
        if self.svg.getElementById("ErrorArrow") is None:
            self._define_marker("ErrorArrow", "#f00")

        if self.svg.getElementById("WarningArrow") is None:
            self._define_marker("WarningArrow", inkex.Color("orange"))

        if self.svg.getElementById("NoteArrow") is None:
            self._define_marker("NoteArrow", "#0f0")

    def _define_marker(self, id, color):
        """define (if it doesn't exist already) a marker for the error arrow
        artefacts"""
        marker = inkex.Marker(id=id,
                              orient='auto',    # orient='auto-start-reverse',
                              markerWidth='3',
                              markerHeight='3',
                              )

        arrow = inkex.PathElement()
        arrow.path = [Move(-3, 3), Line(0, 0), Line(-3, -3)]
        arrow.style = inkex.Style({
            "stroke": color,
            "stroke-width": 1,
            "fill": "none",
        })
        marker.append(arrow)
        self.svg.defs.append(marker)

    def _new_arrow(self, elem, global_transform, width=2, msg=None):
        """add an artefact arrow in the error layer
           elem, global_transform is the element the arrow should be pointing to
        """
        if isinstance(elem, inkex.TextElement):
            # check if it contains a textpath, and compute the corresponding x,y values
            for e in elem:
                if isinstance(e, inkex.TextPath):
                    href = e.get('xlink:href')
                    path = self.svg.getElementById(href[1:])
                    bb = path.shape_box(transform=global_transform)
                    x, y = elem.transform.apply_to_point(inkex.Vector2d(bb.left, bb.bottom))
                    break
            else:
                # otherwise, just use the text's x,y values
                x, y = elem.x, elem.y
        else:
            # for other elements, use the bottom left corner of the bounding box
            bb = elem.shape_box(transform=global_transform)
            x, y = bb.left, bb.bottom
        arrow = inkex.PathElement()
        arrow.path = [Move(x-20, y+20), Line(x-1, y+1)]
        arrow.style = inkex.Style({
            "stroke-width": width,
            "fill": "none",
        })

        # add the message in the description
        if msg is not None:
            desc = inkex.elements.Desc()
            desc.text = msg
            arrow.append(desc)

        # Add the artefact to the error group (inside the error layer)
        self.error_group.add(arrow)

        return arrow

    def new_error_arrow(self, elem, global_transform, width=2, msg=None):
        """add an _error_ arrow (in red)"""
        arrow = self._new_arrow(elem, global_transform, width=width, msg=msg)
        arrow.style["stroke"] = "#f00"
        arrow.style["marker-end"] = "url(#ErrorArrow)"

    def new_warning_arrow(self, elem, global_transform, width=2, msg=None):
        """add a _warning_ arrow (in orange)"""
        arrow = self._new_arrow(elem, global_transform, width=width, msg=msg)
        arrow.style["stroke"] = inkex.Color("orange")
        arrow.style["marker-end"] = "url(#WarningArrow)"

    def new_note_arrow(self, elem, global_transform, width=2, msg=None):
        """add a _note_ arrow (in green)"""
        arrow = self._new_arrow(elem, global_transform, width=width, msg=msg)
        arrow.style["stroke"] = "#0f0"
        arrow.style["marker-end"] = "url(#NoteArrow)"

    def outline_bounding_box(self, elem, global_transform, width=1, color="#f00", msg=None, margin=3):
        """outline the bounding box of elem,global_transform"""
        if isinstance(elem, inkex.TextElement):
            # text don't have real bounding box! even making a robust rough
            # estimation is non trivial
            # bb = elem.get_inkscape_bbox() # very slow!!!
            # TODO: for TextPath, I could show the bounding box of the path,
            # after aplying the TextPath transform.
            return
        else:
            bb = elem.shape_box(transform=global_transform)

        rect = inkex.Rectangle(x=str(bb.left-margin), y=str(bb.top-margin),
                               width=str(bb.width+2*margin),
                               height=str(bb.height+2*margin))
        rect.style = inkex.Style({
            "fill": "none",
            "stroke": color,
            "stroke-width": width,
        })
        self.error_group.add(rect)

    def clean(self, force=False):
        """remove the error layer / error group if it is empty
        If force is true, remove it even if it is not empty"""
        svg = self.svg

        error_layer = svg.getElementById("ErrorLayer")
        error_group = svg.getElementById("ErrorGroup")

        if error_group is not None and (force or len(error_group) == 0):
            error_group.clear()
            error_group.getparent().remove(error_group)

        if error_layer is not None and (force or len(error_layer) == 0):
            error_layer.clear()
            error_layer.getparent().remove(error_layer)

        if force or len(error_layer) == 0:
            marker = svg.getElementById("ErrorArrow")
            if marker is not None:
                marker.getparent().remove(marker)
            marker = svg.getElementById("WarningArrow")
            if marker is not None:
                marker.getparent().remove(marker)
            marker = svg.getElementById("NoteArrow")
            if marker is not None:
                marker.getparent().remove(marker)
