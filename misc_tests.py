#!/usr/bin/env python
# coding=utf-8

import inkex


class MiscTests(inkex.EffectExtension):

    def init_error(self):
        error_layer = self.svg.getElementById("ErrorLayer")

        if error_layer is not None and error_layer.get('inkscape:groupmode') == 'layer':
            self.error_layer = error_layer
            self.error_layer.clear()     # remove all elements in error layer (and layer itself!)

        root = self.document.getroot()

        # Create a new layer (group with groupmode 'layer')
        error_layer = inkex.Group.new('ERRORS')
        error_layer.set('inkscape:groupmode', 'layer')
        error_layer.set('inkscape:label', 'ERRORS')
        error_layer.set("id", "ErrorLayer")
        root.add(error_layer)
        self.error_layer = error_layer

        # and define the arrow marker
        defs = self.svg.defs
        if defs.find(".//svg:marker[@id='ErrorArrow']", namespaces=inkex.NSS) is not None:
            # if it already exists, do nothing
            return

        marker = inkex.Marker(id='ErrorArrow',
                              orient='auto-start-reverse',
                              refX='0',
                              refY='0',
                              markerWidth='3',
                              markerHeight='3',
                              viewBox='0 0 3 3')

        arrow = inkex.PathElement()
        arrow.path = "M -3,3 L 0,0 L -3,-3"
        arrow.style = inkex.Style({
            "stroke": "#f00",
            "stroke-width": "1",
            "fill": "none",
        })
        marker.append(arrow)
        defs.append(marker)

    def new_error(self, x, y):
        # Create a line from point (10, 10) to (100, 100)
        arrow = inkex.PathElement()
        arrow.style = inkex.Style({
            "stroke": "#f00",
            "stroke-width": "3",
            "fill": "none",
            "marker-end": "url(#ErrorArrow)",
        })
        arrow.path = f"M {x-25},{y-25} L {x},{y}"

        # Add the line to the current layer
        self.error_layer.add(arrow)

    def add_arguments(self, pars):
        pass    # We don't need arguments for this extension

    def effect(self):
        # make sure the unit is "mm"
        self.svg.namedview.set(inkex.addNS('document-units', 'inkscape'), 'mm')

        self.init_error()

        # mark the selected elements
        for elem in self.svg.selection:
            if elem is None:
                # error elements (in the error layer) that could have been
                # selected have been cleared by the init_error method
                # they don't have a bounding box and we shouldn't tag them
                # anyway!
                continue
            bb = elem.bounding_box()
            if bb is None:
                # see above
                continue
            self.new_error(bb.left, bb.top)


if __name__ == '__main__':
    MiscTests().run()
