#!/usr/bin/env python
# coding=utf-8

import inkex
from lib import config
from inkex.paths import Move, Line


skip_tags = {       # TODO: wouldn't it be better to have a white list instead of a black list?
    inkex.addNS('defs', 'svg'),
    inkex.addNS('desc', 'svg'),
    inkex.addNS('metadata', 'svg'),
    inkex.addNS('namedview', 'sodipodi'),
    inkex.addNS('script', 'svg'),
    inkex.addNS('style', 'svg'),
}


def iter_elements(
    elem,                       # current element
    recurse=True,               # should we recurse inside groups?
    skip_groups=False,          # should we return group elements?
    global_transform=None,      # current transformation wrt root, accumulate transformation while going inside groups
    limit=None,                 # current limit for total number of returned elements
                                # if None, there is no limit; otherwise, limit should be a list with a single element
                                # that decreases each time we "yield" an element
):
    global_transform = global_transform or inkex.transforms.Transform()
    if limit is not None and limit[0] <= 0:
        return

    # skip error layer
    if elem.get("id") == "ErrorLayer":
        return

    # skip non SVG elements
    if elem.tag in skip_tags:
        return

    if not isinstance(elem, inkex.Group) or not skip_groups:
        yield elem, global_transform
        if limit is not None:
            limit[0] -= 1

    # don't recurse in non-groups, or if recurse is False
    if not isinstance(elem, inkex.Group) or not recurse:
        return

    # TODO: I shouldn't update global_transform on layers???

    for e in elem:
        if isinstance(e, inkex.Group):
            # tr = global_transform
            tr = global_transform @ elem.transform
            # tr = global_transform @ elem.getparent().transform
        else:
            # tr = global_transform
            tr = global_transform @ elem.transform
            # tr = global_transform @ elem.getparent().transform
        yield from iter_elements(e,
                                 recurse=recurse,
                                 skip_groups=skip_groups,
                                 global_transform=tr,
                                 limit=limit,
                                 )


class FablabExtension(config.ConfigExt):

    def selected_or_all(self, recurse=False, skip_groups=False, limit=None):
        if limit is not None:
            limit = [limit]
        if not self.svg.selected:
            for elem in self.svg:
                yield from iter_elements(elem, recurse=recurse, skip_groups=skip_groups, limit=limit)
        else:
            for elem in self.svg.selected:
                if not isinstance(elem, inkex.Group):
                    tr = elem.getparent().composed_transform()
                else:
                    tr = elem.composed_transform()
                yield from iter_elements(elem, recurse=recurse,
                                         skip_groups=skip_groups,
                                         global_transform=tr,
                                         limit=limit)

    def all_elements(self, recurse=False, skip_groups=False, limit=None):
        if limit is not None:
            limit = [limit]

    def init(self):
        # make sure the unit is "mm"
        self.svg.namedview.set(inkex.addNS('document-units', 'inkscape'), 'mm')

    def init_error_layer(self):
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
        error_layer.set_sensitive(False)
        root.add(error_layer)

        # and create Inkscape group inside
        self.error_group = inkex.Group()
        self.error_group.set("id", "ErrorGroup")
        error_layer.add(self.error_group)

        # define the arrow markers
        defs = self.svg.defs
        if defs.find(".//svg:marker[@id='ErrorArrow']", namespaces=inkex.NSS) is None:
            self._define_marker("ErrorArrow", "#f00")

        if defs.find(".//svg:marker[@id='WarningArrow']", namespaces=inkex.NSS) is None:
            self._define_marker("WarningArrow", inkex.Color("orange"))

        if defs.find(".//svg:marker[@id='NoteArrow']", namespaces=inkex.NSS) is None:
            self._define_marker("NoteArrow", "#0f0")

    def _define_marker(self, id, color):
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
        if isinstance(elem, inkex.TextElement):
            # check if it contains a textpath, and compute the x,y values if
            # so
            for e in elem:
                if isinstance(e, inkex.TextPath):
                    href = e.get('xlink:href')
                    path = self.svg.getElementById(href[1:])
                    bb = path.shape_box(transform=global_transform)
                    v = elem.transform.apply_to_point(inkex.Vector2d(bb.left, bb.bottom))
                    x, y = v.x, v.y
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

        if msg is not None:
            desc = inkex.elements.Desc()
            desc.text = msg
            arrow.append(desc)

        # Add the line to the current layer
        self.error_group.add(arrow)

        return arrow

    def new_error_arrow(self, elem, global_transform, width=2, msg=None):
        arrow = self._new_arrow(elem, global_transform, width=width, msg=msg)
        arrow.style["stroke"] = "#f00"
        arrow.style["marker-end"] = "url(#ErrorArrow)"

    def new_warning_arrow(self, elem, global_transform, width=2, msg=None):
        arrow = self._new_arrow(elem, global_transform, width=width, msg=msg)
        arrow.style["stroke"] = inkex.Color("orange")
        arrow.style["marker-end"] = "url(#WarningArrow)"

    def new_note_arrow(self, elem, global_transform, width=2, msg=None):
        arrow = self._new_arrow(elem, global_transform, width=width, msg=msg)
        arrow.style["stroke"] = "#0f0"
        arrow.style["marker-end"] = "url(#NoteArrow)"

    def outline_bounding_box(self, elem, global_transform, width=1, color="#f00", msg=None, margin=3):
        if isinstance(elem, inkex.TextElement):
            # text don't have real bounding box! even making a robust rough
            # estimation is non trivial
            # bb = elem.get_inkscape_bbox() # very slow!!!
            return
        else:
            bb = elem.shape_box(transform=global_transform)
            # bb = elem.shape_box()

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
        error_layer = self.svg.getElementById("ErrorLayer")
        error_group = self.svg.getElementById("ErrorGroup")

        if error_group is not None and (force or len(error_group) == 0):
            error_group.clear()
            error_group.getparent().remove(error_group)

        if error_layer is not None and (force or len(error_layer) == 0):
            error_layer.clear()
            error_layer.getparent().remove(error_layer)

        if force or len(error_layer) == 0:
            defs = self.svg.defs
            marker = defs.find(".//svg:marker[@id='ErrorArrow']", namespaces=inkex.NSS)
            if marker is not None:
                marker.getparent().remove(marker)
            marker = defs.find(".//svg:marker[@id='WarningArrow']", namespaces=inkex.NSS)
            if marker is not None:
                marker.getparent().remove(marker)
            marker = defs.find(".//svg:marker[@id='NoteArrow']", namespaces=inkex.NSS)
            if marker is not None:
                marker.getparent().remove(marker)


class ChangeStyle(FablabExtension):

    def __init__(self, mode="line", color=None, fill=None, width=None):
        super().__init__()
        self.new_color = color or self.config.get(f"laser_mode_{mode}_color")
        self.new_fill = fill or "none"
        self.new_width = width or self.config.get("misc_laser_diameter")

    def add_arguments(self, pars):
        pass    # We don't need arguments for this extension

    def effect(self):
        if not self.svg.selected:
            raise inkex.AbortExtension("YOU MUST SELECT AT LEAST ONE ELEMENT")
        self.init()
        self.init_error_layer()

        # TODO should I apply to all elements if the selection is empty?
        # TODO should I tag text blocks
        for elem, tr in self.selected_or_all(recurse=True,
                                             skip_groups=True,
                                             limit=None):
            if self.new_color:
                elem.style["stroke"] = self.new_color
            if self.new_width:
                elem.style["stroke-width"] = self.new_width
            if self.new_fill:
                elem.style["fill"] = self.new_fill
