#!/usr/bin/env python

from tempfile import TemporaryDirectory
import copy
import time

import inkex
from inkex.paths import Move, Line

from lib import i18n, config, utils


ARTEFACT_CLASS = "artefact"
ARTEFACT_LAYER_ID = "ArtefactLayer"
ARTEFACT_GROUP_ID = "ArtefactGroup"
ARTEFACT_OVERLAY_ID = "ArtefactOverlay"
ARTEFACT_OVERLAY_PATTERN_ID = "ArtefactOverlayPattern"

# error levels
OK = 0
NOTE = 1
WARNING = 2
ERROR = 3

NOTE_COLOR = "#00ff00"      # green
WARNING_COLOR = "#ffa500"   # orange
ERROR_COLOR = "#ff0000"     # red


# TODO: I should look for a list of valid tags, to check what I am missing!
# It might be better to use a white list of tags rather than a black list.
def _skip_meta(elem):
    """return true if the elem should be skipped as part of metadata"""
    return any((isinstance(elem, cls) for cls in
                [inkex.Defs, inkex.Desc, inkex.Metadata,
                 inkex.NamedView, inkex.Script, inkex.Style]))


def composed_transform(elem):
    parent = elem.getparent()
    inkex.utils.debug(f"  parent => {parent}")
    if isinstance(parent, inkex.BaseElement):
        return composed_transform(parent) @ elem.transform
    return elem.transform


# NOTE: the _iter_element method doesn't really need to compute the
# _global_transform on the fly as it is available with
# elem.getparent().composed_transform()
# It is however faster to compute it on the fly, at least theoretically.
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

    if not isinstance(elem, inkex.Group) or not skip_groups or isinstance(elem, inkex.Layer):
        yield elem, _global_transform
        # yield elem, elem.getparent().composed_transform()
        # this is functionnaly equivalent, but could be slower if the elements tree is huge
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
                                  _global_transform=_global_transform @ elem.transform)


def _set_text_style(elem, **style):
    elem.style = inkex.Style(elem.attrib.get("style", ""))
    for k in style:
        elem.style[k.replace("_", "-")] = style[k]
        # since values could be inkex objects (like Color), I need to transform the value to a string
        elem.attrib[k.replace("_", "-")] = str(style[k])

    # Recurse into child nodes (tspan, textPath, etc.)
    for e in elem:
        _set_text_style(e, **style)


class Ext(inkex.EffectExtension, config.Ext, i18n.Ext):

    def __init__(self, reset_artefacts=True):
        super().__init__()
        i18n.Ext.__init__(self)
        config.Ext.__init__(self)
        self.reset_artefacts = reset_artefacts
        self._start_time = time.perf_counter()
        self.missing_bb = []

    def running_time(self):
        return 1000*(time.perf_counter() - self._start_time)

    def message(self, *args, verbosity=0, end="", sep=" "):
        if verbosity > self.config.get("verbosity", 1):
            return
        self.msg(sep.join(str(a) for a in args if a is not None) + end)

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

        # make sure inkscape's unit is "mm"
        svg.namedview.set("inkscape:document-units", "mm")

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
            artefact_layer = inkex.Layer.new(ARTEFACT_LAYER_ID, id=ARTEFACT_LAYER_ID)
            artefact_layer.set("class", ARTEFACT_CLASS)
            if self.config["artefacts_locked"]:
                artefact_layer.set_sensitive(False)
            root.add(artefact_layer)           # insert last, ie at top
            # to insert first, ie on the bottom, use
            # root.insert(0, artefact_layer)

        # and create Inkscape group inside
        if artefact_group is None:
            if self.config["artefacts_grouped"]:
                self.artefact_group = inkex.Group(id=ARTEFACT_GROUP_ID)
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

        # define the overlay pattern
        artefact_pattern = svg.getElementById(ARTEFACT_OVERLAY_PATTERN_ID)
        if artefact_pattern is None:
            artefact_pattern = inkex.Pattern(id=ARTEFACT_OVERLAY_PATTERN_ID)
            artefact_pattern.set("patternUnits", "userSpaceOnUse")
            artefact_pattern.set("width", 2)
            artefact_pattern.set("height", 1)
            artefact_pattern.set("patternTransform", "rotate(30) scale(5)")
            rect = inkex.Rectangle.new(0, 0, 1, 1)
            rect.style["fill"] = "red"
            rect.style["stroke"] = "none"
            artefact_pattern.add(rect)
            self.svg.defs.add(artefact_pattern)

    def clean(self, force=False):
        """remove the artefact layer / group if it is empty
        If force is true, remove it even if it is not empty"""
        svg = self.svg

        artefact_layer = svg.getElementById(ARTEFACT_LAYER_ID)
        artefact_group = svg.getElementById(ARTEFACT_GROUP_ID)
        artefact_overlay = svg.getElementById(ARTEFACT_OVERLAY_ID)

        if artefact_overlay is not None and force:
            artefact_overlay.getparent().remove(artefact_overlay)

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
            pattern = svg.getElementById(ARTEFACT_OVERLAY_PATTERN_ID)
            if pattern is not None:
                pattern.getparent().remove(pattern)

    def update_overlay(self, bb):
        rect = self.svg.getElementById(ARTEFACT_OVERLAY_ID)
        if rect is None:
            w = self.svg.unittouu(self.svg.viewport_width)
            h = self.svg.unittouu(self.svg.viewport_height)
            rect = inkex.Rectangle.new(0, 0, w, h)
            rect.set("id", ARTEFACT_OVERLAY_ID)
            rect.set("class", ARTEFACT_CLASS)
            rect.set_sensitive(False)
            rect.style = inkex.Style({
                "fill": f"url(#{ARTEFACT_OVERLAY_PATTERN_ID})",
                "opacity": self.config["artefacts_overlay_opacity"]/100,
                "stroke": "none",
                "stroke-width": "1px",
            })
            if self.config["artefacts_grouped"]:
                artefact_group = self.svg.getElementById(ARTEFACT_GROUP_ID)
                artefact_group.add(rect)
            else:
                artefact_layer = self.svg.getElementById(ARTEFACT_LAYER_ID)
                artefact_layer.add(rect)
        if bb is not None:
            bb = bb + rect.shape_box()
            rect.set("x", bb.left)
            rect.set("y", bb.top)
            rect.set("width", bb.width)
            rect.set("height", bb.height)

    def extract_non_artefacts(self):
        """look through the artefact layer and move all non-artefact outside"""
        artefact_layer = self.svg.getElementById(ARTEFACT_LAYER_ID)
        artefact_bg_layer = self.svg.getElementById(ARTEFACT_LAYER_ID)

        counter = 0
        for layer in [artefact_layer, artefact_bg_layer]:
            if layer is None:
                continue
            for elem, tr in _iter_elements(layer, recurse=True,
                                           skip_groups=False,
                                           skip_artefacts=False,
                                           ):
                cl = elem.get("class")
                if cl and ARTEFACT_CLASS in cl:
                    continue
                counter += 1
                self.message("\t-", f"object with id=#{elem.get_id()} was moved out of the artefact layer",
                             verbosity=2)
                elem.getparent().remove(elem)
                elem.transform = tr
                self.svg.add(elem)
            if counter > 0:
                self.message(f"{counter} object(s) were moved out of the artefact layer",
                             verbosity=1)

    def get_inkscape_bboxes(self, *elems):
        """uses the inkscape command to query the actual bounding boxes of the
        given elements
        It generalizes the get_inkscape_bbox method of text elements by
          - querying more than 1 bounding box, which makes is faster on multiple
            elements
          - working with clones ('use' elements) as well
        """

        ids = ",".join([elem.get_id() for elem in elems])

        with TemporaryDirectory(prefix="inkscape-command") as tmpdir:
            svg_file = inkex.command.write_svg(self.svg.root, tmpdir, "input.svg")
            out = inkex.command.inkscape(svg_file, "-X", "-Y", "-W", "-H", query_id=ids).splitlines()
            if len(out) != 4:
                raise ValueError("Error: Bounding box computation failed")
            X = list(map(self.svg.root.viewport_to_unit, out[0].split(",")))
            Y = list(map(self.svg.root.viewport_to_unit, out[1].split(",")))
            W = list(map(self.svg.root.viewport_to_unit, out[2].split(",")))
            H = list(map(self.svg.root.viewport_to_unit, out[3].split(",")))
            return [inkex.transforms.BoundingBox.new_xywh(*dims) for dims in zip(X, Y, W, H)]

    def mm_to_svg(self, d):
        return inkex.units.convert_unit(self.svg.viewport_to_unit(d), "", "mm")

    def svg_to_mm(self, d):
        return self.svg.unit_to_viewport(inkex.units.convert_unit(d, "mm"))

    def outline_bounding_box(self, level, elem, transform=None, bb=None, msg=None, margin=1, **style):
        """outline the bounding box of elem,global_transform
        Fails on text elements (whose bounding box cannot be computed easily)
        except when parameter accepts_text is true. In this case, the
        "get_inkscape_bb" method is used, but it is very slow. (It calls an
        external inkscape process!)"""
        if elem is None and bb is None:
            self.abort("ERROR: method `outline_bounding_box` needs either an SVG element or an explicit bounding box")

        if elem is None:
            id = self.svg.get_unique_id("artefact_bb")
        else:
            id = f"{ARTEFACT_CLASS}_boundingbox_{elem.get_id()}"

        if bb is None:
            bb = utils.bounding_box(elem, transform)
        if bb is None:
            self.missing_bb.append((level, elem, id, msg, margin, style))
            return

        self.__new_artefact_bb(level, bb, id=id, msg=msg, margin=margin, **style)
        if level > NOTE:
            self.update_overlay(bb)

    def outline_missing_bounding_boxes(self):
        elems = [elem for (_, elem, _, _, _, _) in self.missing_bb]
        bbs = self.get_inkscape_bboxes(*elems)
        for bb, (level, _, id, msg, margin, style) in zip(bbs, self.missing_bb):
            self.__new_artefact_bb(level, bb, id=id, msg=msg, margin=margin, **style)
            if level > NOTE:
                self.update_overlay(bb)
        self.missing_bb = []

    def outline_arrow(self, level, elem, transform=None, p=None, msg=None, margin=1,
                      **style):
        if elem is None and p is None:
            self.abort("ERROR: method `outline_arrow` needs either an SVG element or an explicit point")

        if p is None:
            # FIXME: clean this code!
            if isinstance(elem, inkex.TextElement):
                # check if it contains a textpath, and compute the corresponding x,y values
                for e in elem:
                    if isinstance(e, inkex.TextPath):
                        href = e.get("xlink:href")
                        path = self.svg.getElementById(href[1:])
                        bb = path.bounding_box(transform=transform)
                        p = elem.transform.apply_to_point(inkex.Vector2d(bb.left, bb.bottom))
                        break
                else:
                    # otherwise, just use the text's x,y values
                    if transform is not None:
                        p = transform.apply_to_point(inkex.Vector2d(elem.x, elem.y))
                    else:
                        p = (elem.x, elem.y)
            else:
                # for other elements, use the bottom left corner of the bounding box
                bb = elem.bounding_box(transform=transform)
                p = (bb.left, bb.bottom)
        else:
            # p is explicitly given, do nothing
            # TODO: should I apply transform if it is given as well?
            pass

        x, y = p

        if elem is None:
            id = self.svg.get_unique_id("artefact_arrow")
        else:
            id = f"{ARTEFACT_CLASS}_arrow_{elem.get_id()}"

        self._new_artefact_arrow(level, x, y, id, length=10, msg=msg, margin=margin, **style)

        if level > NOTE:
            self.update_overlay(inkex.BoundingBox())

    def outline_text(self, level, elem, global_transform, msg=None, **style):
        # FIXME: clean
        stroke_width = self.config["artefacts_stroke_width"]/3

        if level == OK:
            stroke = NOTE_COLOR
            stroke_width = stroke_width/2
        elif level == NOTE:
            stroke = NOTE_COLOR
        elif level == WARNING:
            stroke = WARNING_COLOR
        elif level == ERROR:
            stroke = ERROR_COLOR
        else:
            assert False    # FIXME
        if "stroke" not in style:
            style["stroke"] = stroke

        clone = copy.deepcopy(elem)
        clone.set("class", ARTEFACT_CLASS)
        clone.transform = clone.transform @ global_transform
        style["stroke-width"] = self.mm_to_svg(stroke_width)
        _set_text_style(clone, **style)
        # add the message in the description
        if msg is not None:
            desc = inkex.elements.Desc()
            desc.text = msg
            clone.append(desc)
        self.artefact_group.add(clone)

    def _new_marker(self, id, color):
        """define an arrowhead marker for the arrow artefacts"""
        marker = inkex.Marker(id=id,
                              orient="auto",    # orient='auto-start-reverse',
                              markerWidth="3",
                              markerHeight="3",
                              )
        marker.set("class", ARTEFACT_CLASS)

        arrow = inkex.PathElement()
        arrow.set("class", ARTEFACT_CLASS)
        arrow.path = [Move(-3, 3), Line(0, 0), Line(-3, -3)]
        arrow.style = inkex.Style({
            "stroke": color,
            "stroke-width": 1,
            "fill": "none",
            # "stroke-opacity": self.config["artefacts_opacity"]/100,
        })
        marker.append(arrow)
        self.svg.defs.append(marker)

    def __new_artefact_bb(self, level, bb, id, msg=None, margin=1, **style):
        rect = self.svg.getElementById(id)
        if rect is None:
            margin = self.mm_to_svg(margin)
            x, y = bb.left, bb.top
            w, h = bb.width, bb.height
            rect = inkex.Rectangle.new(x-margin, y-margin, w+2*margin, h+2*margin)
            rect.set("id", id)
            rect.set("class", ARTEFACT_CLASS)
            rect.style = inkex.Style({
                "error-level": -1,       # custom style attribute
            })

        # add the message in the description
        if msg is not None:
            desc = rect.desc or ""
            desc += msg + "\n"
            rect.desc = desc

        if int(rect.style.get("error-level")) > level:
            # existing bounding box has higher error-level: keep existing style
            return

        rect.style["error-level"] = level
        rect.style["fill"] = "none"
        rect.style["stroke-opacity"] = self.config["artefacts_opacity"]/100
        rect.style["stroke-width"] = self.config["artefacts_stroke_width"]

        if level == OK:
            rect.style["stroke"] = NOTE_COLOR
            rect.style["stroke-width"] = float(rect.style["stroke-width"]) / 2
        elif level == NOTE:
            rect.style["stroke"] = NOTE_COLOR
        elif level == WARNING:
            rect.style["stroke"] = WARNING_COLOR
        elif level == ERROR:
            rect.style["stroke"] = ERROR_COLOR
        else:
            assert False    # FIXME

        for k in style:
            rect.style[k.replace("_", "-")] = style[k]
        self.artefact_group.add(rect)

        # convert stroke-width to actual mm
        rect.style["stroke-width"] = self.mm_to_svg(rect.style["stroke-width"])

    def _new_artefact_arrow(self, level, x, y, id, msg=None, length=10, margin=1, **style):
        """add an artefact arrow in the error layer
           elem, global_transform is the element the arrow should be pointing to
        """
        arrow = self.svg.getElementById(id)
        if arrow is None:
            side = self.mm_to_svg(length)
            margin = self.mm_to_svg(margin)
            arrow = inkex.PathElement()
            arrow.set("id", id)
            arrow.set("class", ARTEFACT_CLASS)
            arrow.path = [Move(x-side, y+side),
                          Line(x-margin, y+margin)]
            arrow.style = inkex.Style({
                "error-level": -1,       # custom style attribute
            })

        # add the message in the description
        if msg is not None:
            desc = arrow.desc or ""
            desc += msg + "\n"
            arrow.desc = desc

        if int(arrow.style.get("error-level")) > level:
            # existing  arrow has higher error-level: keep existing style
            return

        arrow.style["error-level"] = level
        arrow.style["fill"] = "none"
        arrow.style["opacity"] = self.config["artefacts_opacity"]/100
        arrow.style["stroke-width"] = self.config["artefacts_stroke_width"]

        if level == OK:
            arrow.style["stroke"] = NOTE_COLOR
            arrow.style["stroke-width"] = float(arrow.style["stroke-width"]) / 2
            arrow.style["marker-end"] = "url(#NoteArrowheadMarker)"
        elif level == NOTE:
            arrow.style["stroke"] = NOTE_COLOR
            arrow.style["marker-end"] = "url(#NoteArrowheadMarker)"
        elif level == WARNING:
            arrow.style["stroke"] = WARNING_COLOR
            arrow.style["marker-end"] = "url(#WarningArrowheadMarker)"
        elif level == ERROR:
            arrow.style["stroke"] = ERROR_COLOR
            arrow.style["marker-end"] = "url(#ErrorArrowheadMarker)"
        else:
            assert False    # FIXME

        for k in style:
            arrow.style[k.replace("_", "-")] = style[k]
        self.artefact_group.add(arrow)

        # Add the artefact to the error group (inside the error layer)
        self.artefact_group.add(arrow)

        # convert stroke-width to actual mm
        arrow.style["stroke-width"] = self.mm_to_svg(arrow.style["stroke-width"])

    def abort(self, *args, header=None, end="\n", sep=" "):
        if header is None:
            header = """
Error encountered while running extension, aborting.

details:
"""
        raise inkex.AbortExtension(header + sep.join(str(a) for a in args if a is not None) + end)


# vim: textwidth=120 foldmethod=indent foldlevel=0
