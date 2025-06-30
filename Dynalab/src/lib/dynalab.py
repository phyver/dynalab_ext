#!/usr/bin/env python

from tempfile import TemporaryDirectory
import copy
import time

import inkex
from inkex.paths import Move, Line

from lib import i18n, config, utils


ARTIFACT_CLASS = "artifact"
ARTIFACT_LAYER_ID = "ArtifactLayer"
ARTIFACT_GROUP_ID = "ArtifactGroup"
ARTIFACT_OVERLAY_ID = "ArtifactOverlay"
ARTIFACT_OVERLAY_PATTERN_ID = "ArtifactOverlayPattern"

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


# NOTE: the _iter_element method doesn't really need to compute the
# _global_transform on the fly as it is available with
# elem.getparent().composed_transform()
# It is however faster to compute it on the fly, at least theoretically.
# TODO: add arguments
#  - skip_use / recurse_use
#  - skip_symbol / recurse_symbol is not necessary because Symbol inherits from Group
#  - ?? skip_locked
#  - ??? what to do with clippath
def _iter_elements(
    elem,                       # current element
    recurse_groups=True,        # should we recurse inside groups?
    skip_groups=False,          # should we return group elements?
    skip_artifacts=True,        # should we skip artifacts?
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

    # skip artifacts
    if skip_artifacts and elem.get("class") == ARTIFACT_CLASS:
        return

    # skip non SVG elements
    if _skip_meta(elem):
        return

    if not isinstance(elem, inkex.Group) or not skip_groups:
        yield elem, _global_transform
        # yield elem, elem.getparent().composed_transform()
        # this is functionnaly equivalent, but could be slower if the elements tree is huge
        if limit is not None:
            limit[0] -= 1

    # don't recurse in non-groups, or if recurse_groups is False
    if not isinstance(elem, inkex.Group) or not recurse_groups:
        return

    for e in elem:
        yield from _iter_elements(e,
                                  recurse_groups=recurse_groups,
                                  skip_groups=skip_groups,
                                  limit=limit,
                                  skip_artifacts=skip_artifacts,
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

    def __init__(self, reset_artifacts=True):
        super().__init__()
        i18n.Ext.__init__(self)
        config.Ext.__init__(self)
        self.reset_artifacts = reset_artifacts
        self._start_time = time.perf_counter()
        self.BB = {}

    def get_all_bounding_boxes(self):
        with TemporaryDirectory(prefix="inkscape-command") as tmpdir:
            svg_file = inkex.command.write_svg(self.svg.root, tmpdir, "input.svg")
            out = inkex.command.inkscape(svg_file, "--query-all").splitlines()
            for line in out:
                id, x, y, w, h = line.split(",")
                x = self.svg.viewport_to_unit(x)
                y = self.svg.viewport_to_unit(y)
                w = self.svg.viewport_to_unit(w)
                h = self.svg.viewport_to_unit(h)
                self.BB[id] = inkex.BoundingBox.new_xywh(x, y, w, h)

    def bounding_box(self, elem):
        k = elem.get_id()
        if self.BB:
            bb = self.BB.get(k, inkex.BoundingBox())
            return bb

        bb = utils.bounding_box(elem, elem.getparent().composed_transform())
        if bb is not None:
            return bb
        else:
            self.get_all_bounding_boxes()
            bb = self.BB.get(k, inkex.BoundingBox())
            return bb

    def running_time(self):
        return 1000*(time.perf_counter() - self._start_time)

    def message(self, *args, verbosity=0, end="", sep=" "):
        if verbosity > self.config.get("verbosity", 1):
            return
        self.msg(sep.join(str(a) for a in args if a is not None) + end)

    def selected_or_all(self, recurse_groups=True, skip_groups=False, limit=None):
        """iterates over the selected elements (recursively if needs be), or
        all the element if the selection is empty"""
        if limit is not None:
            limit = [limit]
        if not self.svg.selected:
            for elem in self.svg:
                yield from _iter_elements(elem,
                                          recurse_groups=recurse_groups,
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
                tr = parent.composed_transform()
                yield from _iter_elements(elem, recurse_groups=recurse_groups,
                                          skip_groups=skip_groups,
                                          limit=limit,
                                          _global_transform=tr)

    def init_artifact_layer(self):
        """create a special layer to put all errors / warning artifacts
        Artifacts are put inside a group in this layer for easy removal.
        If either the group or the layer already exists, it is cleared first.
        """
        root = self.document.getroot()
        svg = self.svg

        # make sure inkscape's unit is "mm"
        svg.namedview.set("inkscape:document-units", "mm")

        # extract non-artifacts from the artifact layer
        self.extract_non_artifacts()

        # re-initialise existing artifact layer / group
        artifact_layer = svg.getElementById(ARTIFACT_LAYER_ID)
        artifact_group = svg.getElementById(ARTIFACT_GROUP_ID)
        if artifact_group is not None and self.reset_artifacts:
            artifact_group.clear()
            artifact_group.getparent().remove(artifact_group)
            artifact_group = None
        if artifact_layer is not None and self.reset_artifacts:
            artifact_layer.clear()
            artifact_layer.getparent().remove(artifact_layer)
            artifact_layer = None

        # Create a new layer (this is just a special SVG group)
        if artifact_layer is None:
            artifact_layer = inkex.Layer.new(ARTIFACT_LAYER_ID, id=ARTIFACT_LAYER_ID)
            artifact_layer.set("class", ARTIFACT_CLASS)
            if self.config["artifacts_locked"]:
                artifact_layer.set_sensitive(False)
            root.add(artifact_layer)           # insert last, ie at top
            # to insert first, ie on the bottom, use
            # root.insert(0, artifact_layer)

        # and create Inkscape group inside
        if artifact_group is None:
            if self.config["artifacts_grouped"]:
                self.artifact_group = inkex.Group(id=ARTIFACT_GROUP_ID)
                self.artifact_group.set("class", ARTIFACT_CLASS)
                artifact_layer.add(self.artifact_group)
            else:
                self.artifact_group = artifact_layer
        else:
            self.artifact_group = artifact_group

        assert self.artifact_group is not None

        # define the arrow markers
        if svg.getElementById("ErrorArrowheadMarker") is None:
            self._new_marker("ErrorArrowheadMarker", ERROR_COLOR)
        if svg.getElementById("WarningArrowheadMarker") is None:
            self._new_marker("WarningArrowheadMarker", WARNING_COLOR)
        if svg.getElementById("NoteArrowheadMarker") is None:
            self._new_marker("NoteArrowheadMarker", NOTE_COLOR)

        # define the overlay pattern
        artifact_pattern = svg.getElementById(ARTIFACT_OVERLAY_PATTERN_ID)
        if artifact_pattern is None:
            artifact_pattern = inkex.Pattern(id=ARTIFACT_OVERLAY_PATTERN_ID)
            artifact_pattern.set("patternUnits", "userSpaceOnUse")
            artifact_pattern.set("width", 2)
            artifact_pattern.set("height", 1)
            artifact_pattern.set("patternTransform", "rotate(30) scale(5)")
            rect = inkex.Rectangle.new(0, 0, 1, 1)
            rect.style["fill"] = "red"
            rect.style["stroke"] = "none"
            artifact_pattern.add(rect)
            self.svg.defs.add(artifact_pattern)

    def clean(self, force=False):
        """remove the artifact layer / group if it is empty
        If force is true, remove it even if it is not empty"""
        svg = self.svg

        artifact_layer = svg.getElementById(ARTIFACT_LAYER_ID)
        artifact_group = svg.getElementById(ARTIFACT_GROUP_ID)
        artifact_overlay = svg.getElementById(ARTIFACT_OVERLAY_ID)

        if artifact_overlay is not None and force:
            artifact_overlay.getparent().remove(artifact_overlay)

        if artifact_group is not None and (force or len(artifact_group) == 0):
            artifact_group.clear()
            artifact_group.getparent().remove(artifact_group)

        if artifact_layer is not None and (force or len(artifact_layer) == 0):
            artifact_layer.clear()
            artifact_layer.getparent().remove(artifact_layer)

        if force or len(artifact_layer) == 0:
            marker = svg.getElementById("ErrorArrowheadMarker")
            if marker is not None:
                marker.getparent().remove(marker)
            marker = svg.getElementById("WarningArrowheadMarker")
            if marker is not None:
                marker.getparent().remove(marker)
            marker = svg.getElementById("NoteArrowheadMarker")
            if marker is not None:
                marker.getparent().remove(marker)
            pattern = svg.getElementById(ARTIFACT_OVERLAY_PATTERN_ID)
            if pattern is not None:
                pattern.getparent().remove(pattern)

    def update_overlay(self, bb):
        rect = self.svg.getElementById(ARTIFACT_OVERLAY_ID)
        if rect is None:
            w = self.svg.unittouu(self.svg.viewport_width)
            h = self.svg.unittouu(self.svg.viewport_height)
            rect = inkex.Rectangle.new(0, 0, w, h)
            rect.set("id", ARTIFACT_OVERLAY_ID)
            rect.set("class", ARTIFACT_CLASS)
            rect.set_sensitive(False)
            rect.style = inkex.Style({
                "fill": f"url(#{ARTIFACT_OVERLAY_PATTERN_ID})",
                "opacity": self.config["artifacts_overlay_opacity"]/100,
                "stroke": "none",
                "stroke-width": "1px",
            })
            if self.config["artifacts_grouped"]:
                artifact_group = self.svg.getElementById(ARTIFACT_GROUP_ID)
                artifact_group.add(rect)
            else:
                artifact_layer = self.svg.getElementById(ARTIFACT_LAYER_ID)
                artifact_layer.add(rect)
        if bb is not None:
            bb = bb + rect.shape_box()
            rect.set("x", bb.left)
            rect.set("y", bb.top)
            rect.set("width", bb.width)
            rect.set("height", bb.height)

    def extract_non_artifacts(self):
        """look through the artifact layer and move all non-artifact outside"""
        artifact_layer = self.svg.getElementById(ARTIFACT_LAYER_ID)
        artifact_bg_layer = self.svg.getElementById(ARTIFACT_LAYER_ID)

        counter = 0
        for layer in [artifact_layer, artifact_bg_layer]:
            if layer is None:
                continue
            for elem, tr in _iter_elements(layer,
                                           skip_groups=False,
                                           skip_artifacts=False,
                                           ):
                cl = elem.get("class")
                if cl and ARTIFACT_CLASS in cl:
                    continue
                counter += 1
                self.message("\t-", f"object with id=#{elem.get_id()} was moved out of the artifact layer",
                             verbosity=2)
                elem.getparent().remove(elem)
                elem.transform = tr
                self.svg.add(elem)
            if counter > 0:
                self.message(f"{counter} object(s) were moved out of the artifact layer",
                             verbosity=1)

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
            id = self.svg.get_unique_id("artifact_bb")
        else:
            id = f"{ARTIFACT_CLASS}_boundingbox_{elem.get_id()}"

        if bb is None:
            bb = self.bounding_box(elem)

        self.__new_artifact_bb(level, bb, id=id, msg=msg, margin=margin, **style)
        if level > NOTE:
            self.update_overlay(bb)

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
                        bb = self.bounding_box(path)
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
                bb = self.bounding_box(elem)
                p = (bb.left, bb.bottom)
        else:
            # p is explicitly given, do nothing
            # TODO: should I apply transform if it is given as well?
            pass

        x, y = p

        if elem is None:
            id = self.svg.get_unique_id("artifact_arrow")
        else:
            id = f"{ARTIFACT_CLASS}_arrow_{elem.get_id()}"

        self._new_artifact_arrow(level, x, y, id, length=10, msg=msg, margin=margin, **style)

        if level > NOTE:
            self.update_overlay(inkex.BoundingBox())

    def outline_element(self, level, elem, transform=None, msg=None, **style):
        if elem is None:
            self.abort("ERROR: method `outline_element` needs an SVG element")
        id = f"{ARTIFACT_CLASS}_element_{elem.get_id()}"
        clone = self.svg.getElementById(id)
        if clone is None:
            clone = copy.deepcopy(elem)
            clone.set("id", id)
            clone.set("class", ARTIFACT_CLASS)
            clone.transform = transform @ elem.transform
            clone.style = inkex.Style({
                "error-level": -1,       # custom style attribute
            })
            # _set_text_style(clone, **style)

        # add the message in the description
        if msg is not None:
            desc = clone.desc or ""
            desc += msg + "\n"
            clone.desc = desc

        if int(clone.style.get("error-level")) > level:
            # existing clone has higher error-level: keep existing style
            return

        clone.style["error-level"] = level
        clone.style["fill"] = "none"
        clone.style["opacity"] = self.config["artifacts_opacity"]/100
        clone.style["stroke-width"] = self.config["artifacts_stroke_width"]

        if level == OK:
            clone.style["stroke"] = NOTE_COLOR
            clone.style["stroke-width"] = float(clone.style["stroke-width"]) / 2
        elif level == NOTE:
            clone.style["stroke"] = NOTE_COLOR
        elif level == WARNING:
            clone.style["stroke"] = WARNING_COLOR
        elif level == ERROR:
            clone.style["stroke"] = ERROR_COLOR
        else:
            assert False    # FIXME

        for k in style:
            clone.style[k.replace("_", "-")] = style[k]
        self.artifact_group.add(clone)

        # Add the artifact to the error group (inside the error layer)
        self.artifact_group.add(clone)

        # convert stroke-width to actual mm
        clone.style["stroke-width"] = self.mm_to_svg(clone.style["stroke-width"])

    def _new_marker(self, id, color):
        """define an arrowhead marker for the arrow artifacts"""
        marker = inkex.Marker(id=id,
                              orient="auto",    # orient='auto-start-reverse',
                              markerWidth="3",
                              markerHeight="3",
                              )
        marker.set("class", ARTIFACT_CLASS)

        arrow = inkex.PathElement()
        arrow.set("class", ARTIFACT_CLASS)
        arrow.path = [Move(-3, 3), Line(0, 0), Line(-3, -3)]
        arrow.style = inkex.Style({
            "stroke": color,
            "stroke-width": 1,
            "fill": "none",
            # "stroke-opacity": self.config["artifacts_opacity"]/100,
        })
        marker.append(arrow)
        self.svg.defs.append(marker)

    def __new_artifact_bb(self, level, bb, id, msg=None, margin=1, **style):
        rect = self.svg.getElementById(id)
        if rect is None:
            margin = self.mm_to_svg(margin)
            x, y = bb.left, bb.top
            w, h = bb.width, bb.height
            rect = inkex.Rectangle.new(x-margin, y-margin, w+2*margin, h+2*margin)
            rect.set("id", id)
            rect.set("class", ARTIFACT_CLASS)
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
        rect.style["stroke-opacity"] = self.config["artifacts_opacity"]/100
        rect.style["stroke-width"] = self.config["artifacts_stroke_width"]

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
        self.artifact_group.add(rect)

        # convert stroke-width to actual mm
        rect.style["stroke-width"] = self.mm_to_svg(rect.style["stroke-width"])

    def _new_artifact_arrow(self, level, x, y, id, msg=None, length=10, margin=1, **style):
        """add an artifact arrow in the error layer
           elem, global_transform is the element the arrow should be pointing to
        """
        arrow = self.svg.getElementById(id)
        if arrow is None:
            side = self.mm_to_svg(length)
            margin = self.mm_to_svg(margin)
            arrow = inkex.PathElement()
            arrow.set("id", id)
            arrow.set("class", ARTIFACT_CLASS)
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
            # existing arrow has higher error-level: keep existing style
            return

        arrow.style["error-level"] = level
        arrow.style["fill"] = "none"
        arrow.style["opacity"] = self.config["artifacts_opacity"]/100
        arrow.style["stroke-width"] = self.config["artifacts_stroke_width"]

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
        self.artifact_group.add(arrow)

        # Add the artifact to the error group (inside the error layer)
        self.artifact_group.add(arrow)

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
