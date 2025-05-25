#!/usr/bin/env python

import copy

import inkex
from inkex.paths import Move, Line


def set_text_error(elem, **kwargs):
    elem.style = inkex.Style(elem.attrib.get("style", ""))
    for k in kwargs:
        elem.style[k.replace("_", "-")] = kwargs[k]
        elem.attrib[k.replace("_", "-")] = kwargs[k]

    # Recurse into child nodes (tspan, textPath, etc.)
    for e in elem:
        set_text_error(e, **kwargs)


class Ext(inkex.EffectExtension):

    def init_error_layer(self):
        """create a special error layer to put all errors / warning artefacts
        Artefacts are put inside a group in this layer for easy removal.
        If either the group or the layer already exists, it is cleared first.
        """
        # make sure the unit is "mm"
        self.svg.namedview.set(inkex.addNS('document-units', 'inkscape'), 'mm')

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
        root.add(error_layer)           # insert last, ie at top
        # root.insert(0, error_layer)     # insert first, ie at bottom

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
                x, y = global_transform.apply_to_point(inkex.Vector2d(elem.x, elem.y))
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

    def clone_text_to_error(self, elem, global_transform, msg=None, **kwargs):
        clone = copy.deepcopy(elem)
        clone.transform = clone.transform @ global_transform
        set_text_error(clone, **kwargs)
        # add the message in the description
        if msg is not None:
            desc = inkex.elements.Desc()
            desc.text = msg
            clone.append(desc)
        self.error_group.add(clone)

    def outline_bounding_box(self, elem, global_transform, msg=None, margin=3, **kwargs):
        """outline the bounding box of elem,global_transform"""
        # TODO: add argument to use get_inkscape_bbox on TextElements
        if isinstance(elem, inkex.TextElement):
            # text don't have real bounding box! even making a robust rough
            # estimation is non trivial
            # bb = elem.get_inkscape_bbox() # very slow!!!
            # TODO: for TextPath, I could show the bounding box of the path,
            # after aplying the TextPath transform.
            return
        else:
            bb = elem.shape_box(transform=global_transform)
            # bb = elem.get_inkscape_bbox()

        rect = inkex.Rectangle(x=str(bb.left-margin), y=str(bb.top-margin),
                               width=str(bb.width+2*margin),
                               height=str(bb.height+2*margin))
        rect.style = inkex.Style({
            "fill": "none",
            "stroke": "#000",
            "stroke-width": "0.1mm",
        })
        for k in kwargs:
            rect.style[k.replace("_", "-")] = kwargs[k]
        self.error_group.add(rect)

        # add the message in the description
        if msg is not None:
            desc = inkex.elements.Desc()
            desc.text = msg
            rect.append(desc)

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
