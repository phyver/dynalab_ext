#!/usr/bin/env python
# coding=utf-8

import inkex
from inkex.paths import Move, Line


class MiscTests(inkex.EffectExtension):

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

        # define the arrow marker
        defs = self.svg.defs
        if defs.find(".//svg:marker[@id='ErrorArrow']", namespaces=inkex.NSS) is not None:
            # if it already exists, do nothing
            return

        marker = inkex.Marker(id='ErrorArrow',
                              orient='auto',    # orient='auto-start-reverse',
                              markerWidth='3',
                              markerHeight='3',
                              )

        arrow = inkex.PathElement()
        arrow.path = [Move(-3, 3), Line(0, 0), Line(-3, -3)]
        arrow.style = inkex.Style({
            "stroke": "#f00",
            "stroke-width": "1",
            "fill": "none",
        })
        marker.append(arrow)
        defs.append(marker)

    def new_error(self, x, y, msg=None):
        # Create a line from point (10, 10) to (100, 100)
        arrow = inkex.PathElement()
        arrow.path = [Move(x-25, y-25), Line(x, y)]
        arrow.style = inkex.Style({
            "stroke": "#f00",
            "stroke-width": "3",
            "fill": "none",
            "marker-end": "url(#ErrorArrow)",
        })

        if msg is not None:
            desc = inkex.elements.Desc()
            desc.text = msg
            arrow.append(desc)

        # Add the line to the current layer
        self.error_group.add(arrow)

    def add_arguments(self, pars):
        pass    # We don't need arguments for this extension

    def effect(self):
        # make sure the unit is "mm"
        self.svg.namedview.set(inkex.addNS('document-units', 'inkscape'), 'mm')

        self.init_error()

        # mark the selected elements
        for elem in self.svg.selection or self.all_objects():
            try:
                bb = elem.bounding_box()
                self.new_error(bb.left, bb.top, "lorem")
            except AttributeError:
                # error elements (in the error layer) that could have been
                # selected have been cleared by the init_error method
                # they don't have a bounding box (elem.bounding_box() returns
                # None, so that bb.left / bb.top raises the AttributeError
                # exception)
                # and we shouldn't tag error objects anyway!
                continue


if __name__ == '__main__':
    MiscTests().run()
