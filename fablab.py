#!/usr/bin/env python
# coding=utf-8

import inkex
from inkex.paths import Move, Line


class FablabExtension(inkex.EffectExtension):

    def all_objects(self):
        tags = [
            "path", "circle", "rect", "line", "polyline", "polygon", "ellipse",
            "text", "image", "use"
        ]
        xpath_expr = " | ".join([f"//svg:{tag}" for tag in tags])
        elems = self.svg.xpath(xpath_expr, namespaces=inkex.NSS)
        ignore = [inkex.addNS('defs', 'svg'), inkex.addNS('marker', 'svg'),
                  inkex.addNS('script', 'svg'), inkex.addNS('style', 'svg')]
        return (el for el in elems
                if el.getparent() is not None and el.getparent().tag not in ignore)

    def init_error(self):
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
        error_layer = inkex.Group.new('ErrorLayer')
        error_layer.set('inkscape:groupmode', 'layer')
        error_layer.set('inkscape:label', 'ErrorLayer')
        error_layer.set("id", "ErrorLayer")
        root.add(error_layer)

        # and create Inkscape group inside
        self.error_group = inkex.Group()
        self.error_group.set("id", "ErrorGroup")
        error_layer.add(self.error_group)

        # define the arrow markers
        defs = self.svg.defs
        if defs.find(".//svg:marker[@id='ErrorArrow']", namespaces=inkex.NSS) is not None:
            # if it already exists, do nothing
            return
        self.define_marker("ErrorArrow", "#f00")

        if defs.find(".//svg:marker[@id='WarningArrow']", namespaces=inkex.NSS) is not None:
            # if it already exists, do nothing
            return
        self.define_marker("WarningArrow", inkex.Color("orange"))

        if defs.find(".//svg:marker[@id='NoteArrow']", namespaces=inkex.NSS) is not None:
            # if it already exists, do nothing
            return
        self.define_marker("NoteArrow", "#0f0")

    def define_marker(self, id, color):
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

    def new_arrow(self, x, y, width=2, msg=None):
        # Create a line from point (10, 10) to (100, 100)
        arrow = inkex.PathElement()
        arrow.path = [Move(x-20, y-20), Line(x, y)]
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

    def new_error_arrow(self, x, y, width=2, msg=None):
        arrow = self.new_arrow(x, y, width=width, msg=msg)
        arrow.style["stroke"] = "#f00"
        arrow.style["marker-end"] = "url(#ErrorArrow)"

    def new_warning_arrow(self, x, y, width=2, msg=None):
        arrow = self.new_arrow(x, y, width=width, msg=msg)
        arrow.style["stroke"] = inkex.Color("orange")
        arrow.style["marker-end"] = "url(#WarningArrow)"

    def new_note_arrow(self, x, y, width=2, msg=None):
        arrow = self.new_arrow(x, y, width=width, msg=msg)
        arrow.style["stroke"] = "#0f0"
        arrow.style["marker-end"] = "url(#NoteArrow)"

    def outline_bounding_box(self, elem, width=1, color="#f00", msg=None, margin=1):
        try:
            bb = elem.bounding_box(transform=True)
            rect = inkex.Rectangle(x=str(bb.left-margin), y=str(bb.top-margin),
                                   width=str(bb.width+2*margin),
                                   height=str(bb.height+2*margin))
            rect.style = inkex.Style({
                "fill": "none",
                "stroke": color,
                "stroke-width": width,
            })
            self.error_group.add(rect)
        except AttributeError:
            pass

    def clean(self):
        error_layer = self.svg.getElementById("ErrorLayer")
        error_group = self.svg.getElementById("ErrorGroup")

        if error_group is not None:
            error_group.clear()
            error_group.getparent().remove(error_group)

        if error_layer is not None:
            error_layer.clear()
            error_layer.getparent().remove(error_layer)

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
