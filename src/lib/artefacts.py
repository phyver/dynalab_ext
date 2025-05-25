#!/usr/bin/env python

import copy

import inkex
from inkex.paths import Move, Line


ARTEFACT_CLASS = "artefact"
ARTEFACT_LAYER_ID = "ArtefactLayer"
ARTEFACT_GROUP_ID = "ArtefactGroup"


def set_text_artefact(elem, **kwargs):
    elem.style = inkex.Style(elem.attrib.get("style", ""))
    for k in kwargs:
        elem.style[k.replace("_", "-")] = kwargs[k]
        elem.attrib[k.replace("_", "-")] = kwargs[k]

    # Recurse into child nodes (tspan, textPath, etc.)
    for e in elem:
        set_text_artefact(e, **kwargs)


class Ext(inkex.EffectExtension):

    def __init__(self, group_artefacts=True, lock_artefacts=False, reset_artefacts=True):
        super().__init__()
        self.group_artefacts = group_artefacts
        self.lock_artefacts = group_artefacts
        self.reset_artefacts = reset_artefacts

    def init_artefact_layer(self):
        """create a special layer to put all errors / warning artefacts
        Artefacts are put inside a group in this layer for easy removal.
        If either the group or the layer already exists, it is cleared first.
        """
        root = self.document.getroot()
        svg = self.svg

        # make sure the unit is "mm"
        svg.namedview.set(inkex.addNS('document-units', 'inkscape'), 'mm')

        # remove existing artefact layer, if it exists
        artefact_layer = svg.getElementById(ARTEFACT_LAYER_ID)
        artefact_group = svg.getElementById(ARTEFACT_GROUP_ID)
        if artefact_group is not None and self.reset_artefacts:
            artefact_group.clear()
            artefact_group.getparent().remove(artefact_group)
            artefact_group = None
        if artefact_layer is not None and self.reset_artefacts:
            artefact_layer.clear()
            artefact_layer.getparent().remove(artefact_layer)
            artefact_layer = None

        # Create a new layer (this is just a special SVG group)
        if artefact_layer is None:
            artefact_layer = inkex.Layer.new(ARTEFACT_LAYER_ID)
            artefact_layer.set("id", ARTEFACT_LAYER_ID)
            artefact_layer.set("class", ARTEFACT_CLASS)
            if self.lock_artefacts:
                artefact_layer.set_sensitive(False)
            root.add(artefact_layer)           # insert last, ie at top
            # to insert first, ie on the bottom, use
            # root.insert(0, artefact_layer)

        # and create Inkscape group inside
        if artefact_group is None:
            if self.group_artefacts:
                self.artefact_group = inkex.Group()
                self.artefact_group.set("id", ARTEFACT_GROUP_ID)
                self.artefact_group.set("class", ARTEFACT_CLASS)
                artefact_layer.add(self.artefact_group)
            else:
                self.artefact_group = self.artefact_layer
        else:
            self.artefact_group = artefact_group

        assert self.artefact_group is not None

        # define the arrow markers
        if svg.getElementById("ErrorArrowheadMarker") is None:
            self._define_marker("ErrorArrowheadMarker", inkex.Color("red"))
        if svg.getElementById("WarningArrowheadMarker") is None:
            self._define_marker("WarningArrowheadMarker", inkex.Color("orange"))
        if svg.getElementById("NoteArrowheadMarker") is None:
            self._define_marker("NoteArrowheadMarker", inkex.Color("green"))

    def _define_marker(self, id, color):
        """define an arrowhead marker for the arrow artefacts"""
        marker = inkex.Marker(id=id,
                              orient='auto',    # orient='auto-start-reverse',
                              markerWidth='3',
                              markerHeight='3',
                              )
        marker.set("class", ARTEFACT_CLASS)

        arrow = inkex.PathElement()
        arrow.set("class", ARTEFACT_CLASS)
        arrow.path = [Move(-3, 3), Line(0, 0), Line(-3, -3)]
        arrow.style = inkex.Style({
            "stroke": color,
            "stroke-width": 1,
            "fill": "none",
        })
        marker.append(arrow)
        self.svg.defs.append(marker)

    def _new_artefact_arrow(self, elem, global_transform, length=20, stroke_width=2, msg=None):
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

        length = length / 2**.5
        arrow = inkex.PathElement()
        arrow.set("class", ARTEFACT_CLASS)
        arrow.path = [Move(x-length, y+length), Line(x-stroke_width/2, y+stroke_width/2)]
        arrow.style = inkex.Style({
            "stroke-width": stroke_width,
            "fill": "none",
        })

        # add the message in the description
        if msg is not None:
            desc = inkex.elements.Desc()
            desc.text = msg
            arrow.append(desc)

        # Add the artefact to the error group (inside the error layer)
        self.artefact_group.add(arrow)

        return arrow

    def new_error_arrow(self, elem, global_transform, stroke_width=2, msg=None):
        """add an _error_ arrow (in red)"""
        arrow = self._new_artefact_arrow(elem, global_transform, stroke_width=stroke_width, msg=msg)
        arrow.style["stroke"] = "#f00"
        arrow.style["marker-end"] = "url(#ErrorArrowheadMarker)"

    def new_warning_arrow(self, elem, global_transform, stroke_width=2, msg=None):
        """add a _warning_ arrow (in orange)"""
        arrow = self._new_artefact_arrow(elem, global_transform, stroke_width=stroke_width, msg=msg)
        arrow.style["stroke"] = inkex.Color("orange")
        arrow.style["marker-end"] = "url(#WarningArrowheadMarker)"

    def new_note_arrow(self, elem, global_transform, stroke_width=2, msg=None):
        """add a _note_ arrow (in green)"""
        arrow = self._new_artefact_arrow(elem, global_transform, stroke_width=stroke_width, msg=msg)
        arrow.style["stroke"] = "#0f0"
        arrow.style["marker-end"] = "url(#NoteArrowheadMarker)"

    def clone_text_to_artefact(self, elem, global_transform, msg=None, **kwargs):
        clone = copy.deepcopy(elem)
        clone.set("class", ARTEFACT_CLASS)
        clone.transform = clone.transform @ global_transform
        set_text_artefact(clone, **kwargs)
        # add the message in the description
        if msg is not None:
            desc = inkex.elements.Desc()
            desc.text = msg
            clone.append(desc)
        self.artefact_group.add(clone)

    def outline_bounding_box(self, elem, global_transform, msg=None,
                             margin=3, accept_text=False, **kwargs):
        """outline the bounding box of elem,global_transform
        Fails on text elements (whose bounding box cannot be computed easily)
        except when parameter accepts_text is true. In this case, the
        "get_inkscape_bb" method is used, but it is very slow. (It calls an
        external inkscape process!)"""
        if isinstance(elem, inkex.TextElement):
            if not accept_text:
                raise inkex.AbortExtension("cannot compute text bounding box (function outline_bounding_box)")
            # very slow!!!
            bb = elem.get_inkscape_bbox()   # no need to apply the global transform
        else:
            bb = elem.shape_box(transform=global_transform)

        rect = inkex.Rectangle(x=str(bb.left-margin), y=str(bb.top-margin),
                               width=str(bb.width+2*margin),
                               height=str(bb.height+2*margin))
        rect.set("class", ARTEFACT_CLASS)
        rect.style = inkex.Style({
            "fill": "none",
            "stroke": "#000",
            "stroke-width": "0.1mm",
        })
        for k in kwargs:
            rect.style[k.replace("_", "-")] = kwargs[k]
        self.artefact_group.add(rect)

        # add the message in the description
        if msg is not None:
            desc = inkex.elements.Desc()
            desc.text = msg
            rect.append(desc)

    def clean(self, force=False):
        """remove the artefact layer / group if it is empty
        If force is true, remove it even if it is not empty"""
        svg = self.svg

        artefact_layer = svg.getElementById(ARTEFACT_LAYER_ID)
        artefact_group = svg.getElementById(ARTEFACT_GROUP_ID)

        if artefact_group is not None and (force or len(artefact_group) == 0):
            artefact_group.clear()
            artefact_group.getparent().remove(artefact_group)

        if artefact_layer is not None and (force or len(artefact_layer) == 0):
            artefact_layer.clear()
            artefact_layer.getparent().remove(artefact_layer)

        if force or len(artefact_layer) == 0:
            marker = svg.getElementById("ErrorArrowheadMarker")
            if marker is not None:
                marker.getparent().remove(marker)
            marker = svg.getElementById("WarningArrowheadMarker")
            if marker is not None:
                marker.getparent().remove(marker)
            marker = svg.getElementById("NoteArrowheadMarker")
            if marker is not None:
                marker.getparent().remove(marker)
