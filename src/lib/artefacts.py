#!/usr/bin/env python

import copy

import inkex
from inkex.paths import Move, Line

from lib import i18n, config


ARTEFACT_CLASS = "artefact"
ARTEFACT_LAYER_ID = "ArtefactLayer"
ARTEFACT_GROUP_ID = "ArtefactGroup"

# error levels
OK = 0
NOTE = 1
WARNING = 2
ERROR = 3

NOTE_COLOR = "#00ff00"      # green
WARNING_COLOR = "#ffa500"   # orange
ERROR_COLOR = "#ff0000"     # red


# TODO: I should look for a list of valid tags, to check what I am missing!
# TODO: it might be better to use a white list of tags rather than a black list
def _skip_meta(elem):
    """return true if the elem should be skipped as part of metadata"""
    return any((isinstance(elem, cls) for cls in
                [inkex.Defs, inkex.Desc, inkex.Metadata,
                 inkex.NamedView, inkex.Script, inkex.Style]))


def _iter_elements(
    elem,                       # current element
    recurse=True,               # should we recurse inside groups?
    skip_groups=False,          # should we return group elements?
    skip_artefacts=True,        # should we skip artefacts?
    limit=None,                 # current limit for total number of returned elements
                                # if None, there is no limit; otherwise, limit should be a list with a single element
                                # that decreases each time we "yield" an element
    _global_transform=None,     # current transformation wrt root, accumulate transformation while going inside groups
):
    """recursively iterates over elements
    returns pairs consisting of an element together with its global
    transformation from the root of the document
    """
    _global_transform = _global_transform or inkex.transforms.Transform()
    if limit is not None and limit[0] <= 0:
        return

    # skip artefacts
    if skip_artefacts and elem.get("class") == ARTEFACT_CLASS:
        return

    # skip non SVG elements
    if _skip_meta(elem):
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
                                  skip_artefacts=skip_artefacts,
                                  _global_transform=elem.transform @ _global_transform)


def _set_text_style(elem, **kwargs):
    elem.style = inkex.Style(elem.attrib.get("style", ""))
    for k in kwargs:
        elem.style[k.replace("_", "-")] = kwargs[k]
        # since values could be inkex objects (like Color), I need to transform the value to a string
        elem.attrib[k.replace("_", "-")] = str(kwargs[k])

    # Recurse into child nodes (tspan, textPath, etc.)
    for e in elem:
        _set_text_style(e, **kwargs)


class Ext(inkex.EffectExtension, config.Ext, i18n.Ext):

    def __init__(self, reset_artefacts=True):
        super().__init__()
        i18n.Ext.__init__(self)
        config.Ext.__init__(self)
        self.group_artefacts = self.config["group_artefacts"]
        self.lock_artefacts = self.config["lock_artefacts"]
        self.reset_artefacts = reset_artefacts

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
                                          skip_artefacts=True,
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
                                          skip_artefacts=True,
                                          limit=limit,
                                          _global_transform=tr)

    def init_artefact_layer(self):
        """create a special layer to put all errors / warning artefacts
        Artefacts are put inside a group in this layer for easy removal.
        If either the group or the layer already exists, it is cleared first.
        """
        root = self.document.getroot()
        svg = self.svg

        # make sure the unit is "mm"
        svg.namedview.set(inkex.addNS('document-units', 'inkscape'), 'mm')

        # extract non-artefacts from the artefact layer
        self.extract_non_artefacts()

        # re-initialise existing artefact layer / group
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
                self.artefact_group = artefact_layer
        else:
            self.artefact_group = artefact_group

        assert self.artefact_group is not None

        # define the arrow markers
        if svg.getElementById("ErrorArrowheadMarker") is None:
            self._new_marker("ErrorArrowheadMarker", ERROR_COLOR)
        if svg.getElementById("WarningArrowheadMarker") is None:
            self._new_marker("WarningArrowheadMarker", WARNING_COLOR)
        if svg.getElementById("NoteArrowheadMarker") is None:
            self._new_marker("NoteArrowheadMarker", NOTE_COLOR)

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

    def extract_non_artefacts(self):
        """look through the artefact layer and move all non-artefact outside"""
        artefact_layer = self.svg.getElementById(ARTEFACT_LAYER_ID)
        if artefact_layer is None:
            return

        for elem, tr in _iter_elements(artefact_layer, recurse=True,
                                       skip_groups=False,
                                       skip_artefacts=False,
                                       ):
            cl = elem.get("class")
            if cl and ARTEFACT_CLASS in cl:
                continue
            self.msg(f"element #{elem.get_id()} moved out of the artefact layer")
            elem.getparent().remove(elem)
            elem.transform = tr
            self.svg.add(elem)

    def outline_bounding_box(self, level, elem, global_transform, msg=None,
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
            bb = elem.bounding_box(transform=global_transform)

        # convert width
        stroke_width = self.config["artefacts_stroke_width"]
        if level == OK:
            stroke = NOTE_COLOR  # green
            stroke_width = stroke_width/2
        elif level == NOTE:
            stroke = NOTE_COLOR
        elif level == WARNING:
            stroke = WARNING_COLOR
        elif level == ERROR:
            stroke = ERROR_COLOR
        else:
            assert False    # FIXME

        stroke_width = inkex.units.convert_unit(f"{stroke_width}mm", "px")
        rect = inkex.Rectangle(x=str(bb.left-margin), y=str(bb.top-margin),
                               width=str(bb.width+2*margin),
                               height=str(bb.height+2*margin))
        rect.set("class", ARTEFACT_CLASS)
        rect.style = inkex.Style({
            "fill": "none",
            "stroke": stroke,
            "stroke-width": stroke_width,
        })
        for k in kwargs:
            rect.style[k.replace("_", "-")] = kwargs[k]
        self.artefact_group.add(rect)

        # add the message in the description
        if msg is not None:
            desc = inkex.elements.Desc()
            desc.text = msg
            rect.append(desc)

    def outline_arrow(self, level, elem, global_transform, msg=None):
        stroke_width = self.config["artefacts_stroke_width"]
        if level == OK:
            stroke = NOTE_COLOR
            stroke_width = stroke_width/2
            marker = "#NoteArrowheadMarker"
        elif level == NOTE:
            stroke = NOTE_COLOR
            marker = "#NoteArrowheadMarker"
        elif level == WARNING:
            stroke = WARNING_COLOR
            marker = "#WarningArrowheadMarker"
        elif level == ERROR:
            stroke = ERROR_COLOR  # red
            marker = "#ErrorArrowheadMarker"
        else:
            assert False    # FIXME

        arrow = self._new_artefact_arrow(elem, global_transform, stroke_width=stroke_width, msg=msg)
        arrow.style["stroke"] = stroke
        arrow.style["marker-end"] = f"url({marker})"

    def outline_text(self, level, elem, global_transform, msg=None, **kwargs):
        stroke_width = self.config["artefacts_stroke_width"]/3
        if level == OK:
            stroke = NOTE_COLOR  # green
            stroke_width = stroke_width/2
        elif level == NOTE:
            stroke = NOTE_COLOR
        elif level == WARNING:
            stroke = WARNING_COLOR
        elif level == ERROR:
            stroke = ERROR_COLOR
        else:
            assert False    # FIXME
        if "stroke" not in kwargs:
            kwargs["stroke"] = stroke

        clone = copy.deepcopy(elem)
        clone.set("class", ARTEFACT_CLASS)
        clone.transform = clone.transform @ global_transform
        kwargs["stroke-width"] = inkex.units.convert_unit(f"{stroke_width}mm", "px")
        _set_text_style(clone, **kwargs)
        # add the message in the description
        if msg is not None:
            desc = inkex.elements.Desc()
            desc.text = msg
            clone.append(desc)
        self.artefact_group.add(clone)

    def _new_marker(self, id, color):
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

    def _new_artefact_arrow(self, elem, global_transform, stroke_width=None, length=None, msg=None):
        """add an artefact arrow in the error layer
           elem, global_transform is the element the arrow should be pointing to
        """
        if stroke_width is None:
            stroke_width = self.config["artefacts_stroke_width"]
        if length is None:
            length = 15*stroke_width
        if isinstance(elem, inkex.TextElement):
            # check if it contains a textpath, and compute the corresponding x,y values
            for e in elem:
                if isinstance(e, inkex.TextPath):
                    href = e.get('xlink:href')
                    path = self.svg.getElementById(href[1:])
                    bb = path.bounding_box(transform=global_transform)
                    x, y = elem.transform.apply_to_point(inkex.Vector2d(bb.left, bb.bottom))
                    break
            else:
                # otherwise, just use the text's x,y values
                x, y = global_transform.apply_to_point(inkex.Vector2d(elem.x, elem.y))
        else:
            # for other elements, use the bottom left corner of the bounding box
            bb = elem.bounding_box(transform=global_transform)
            x, y = bb.left, bb.bottom

        # convert distances to mm
        length = inkex.units.convert_unit(f"{length}mm", "px")
        stroke_width = inkex.units.convert_unit(f"{stroke_width}mm", "px")

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


# vim: textwidth=120 foldmethod=indent foldlevel=0
