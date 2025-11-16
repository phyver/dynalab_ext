#!/usr/bin/env python

import time
from gettext import gettext as _
from gettext import ngettext
from tempfile import TemporaryDirectory

import inkex
from inkex.paths import Line, Move

from lib import config, i18n, utils

ARTIFACT_CLASS = "artifact"
ARTIFACT_LAYER_ID = "ArtifactLayer"
ARTIFACT_GROUP_ID = "ArtifactGroup"
ARTIFACT_OVERLAY_GROUP_ID = "ArtifactOverlayGroup"
ARTIFACT_OVERLAY_ID = "ArtifactOverlay"
ARTIFACT_OVERLAY_BORDER_ID = "ArtifactOverlayBorder"
ARTIFACT_OVERLAY_PATTERN_ID = "ArtifactOverlayPattern"

# error levels
OK = 0
NOTE = 1
WARNING = 2
ERROR = 3

NOTE_COLOR = "#00ff00"  # green
WARNING_COLOR = "#ffa500"  # orange
ERROR_COLOR = "#ff0000"  # red


# It might be better to use a white list of tags rather than a black list.
def _skip_meta(elem):
    """return true if the elem should be skipped as part of metadata"""
    return any(
        (
            isinstance(elem, cls)
            for cls in [inkex.Defs, inkex.Desc, inkex.Metadata, inkex.NamedView, inkex.Script, inkex.Style]
        )
    )


def _iter_elements(
    elem,  # current element
    skip_groups=False,  # should we return group elements
    skip_artifacts=True,  # should we skip artifacts?
):
    """recursively iterates over elements"""
    # skip artifacts
    if skip_artifacts and elem.get("class") == ARTIFACT_CLASS:
        return

    # skip non SVG elements
    if _skip_meta(elem):
        return

    # return visual elements (those that are not a group)
    # or the group itself if "skip_group" is false
    if not isinstance(elem, inkex.Group) or not skip_groups:
        yield elem

    if isinstance(elem, inkex.Group):
        # recurse into groups
        for e in elem:
            yield from _iter_elements(e, skip_groups=skip_groups, skip_artifacts=skip_artifacts)


class Ext(inkex.EffectExtension, config.Ext, i18n.Ext):

    def __init__(self, reset_artifacts=True):
        super().__init__()
        i18n.Ext.__init__(self)
        config.Ext.__init__(self)
        self.reset_artifacts = reset_artifacts
        self._time = {}
        self.set_timer("init")
        self.BB = {}
        # if self.name:
        #     # FIXME: is there a better way to do that?
        #     type(self).__name__ = _(type(self).__name__)

    ################
    # misc methods #
    def mm_to_svg(self, d):
        """convert a distance in real-life mm to SVG document units"""
        return inkex.units.convert_unit(self.svg.viewport_to_unit(d), "", "mm")

    def svg_to_mm(self, d):
        """convert a distance in SVG document units to real-life mm"""
        return self.svg.unit_to_viewport(inkex.units.convert_unit(d, "mm"))

    def message(self, *args, verbosity=0, end="", sep=" "):
        """display an inkscape message during extension run
        The message will only be displayed if the current verbosity
        setting is greater or equal to `verbosity`."""
        if verbosity > self.config.get("verbosity", 1):
            return
        self.msg(sep.join(str(a) for a in args if a is not None) + end)

    def abort(self, *args, header=None, end="\n", sep=" "):
        """abort the extension by raising the appropriate exception"""
        if header is None:
            header = "Error encountered while running extension, aborting.\n\ndetails:\n"
        raise inkex.AbortExtension(header + sep.join(str(a) for a in args if a is not None) + end)

    def get_timer(self, name="init"):
        """return the running time (in milliseconds) since the last call to set_timer(name)"""
        return 1000 * (time.perf_counter() - self._time[name])

    def set_timer(self, s):
        """record the current time for easy timing"""
        self._time[s] = time.perf_counter()

    def selected_or_all(self, skip_groups=False):
        """iterates over the selected elements (recursively if needs be), or
        all the element if the selection is empty"""
        if not self.svg.selected:
            for elem in self.svg:
                yield from _iter_elements(elem, skip_groups=skip_groups)
        else:
            for elem in self.svg.selected:
                parent = elem.getparent()
                if parent is None:
                    # this can happen if the user selected an object in the
                    # error layer, which is removed before running a new
                    # extension
                    continue
                yield from _iter_elements(elem, skip_groups=skip_groups)

    ############################
    # computing bounding boxes #
    def get_all_inkscape_bboxes(self):
        """computes a dictionary indexed by ids containing all bounding boxes
        It is similar to inkex' get_inkscape_bbox method for text elements but
        uses the "--query-all" flag to get all bounding boxes with a single
        inkscape invocation. We thus don't have to call the external inkscape
        more than once.
        """
        BB = {}
        with TemporaryDirectory(prefix="inkscape-command") as tmpdir:
            svg_file = inkex.command.write_svg(self.svg.root, tmpdir, "input.svg")
            out = inkex.command.inkscape(svg_file, "--query-all").splitlines()
            for line in out:
                try:
                    id, x, y, w, h = line.split(",")
                    x = self.svg.viewport_to_unit(x)
                    y = self.svg.viewport_to_unit(y)
                    w = self.svg.viewport_to_unit(w)
                    h = self.svg.viewport_to_unit(h)
                    BB[id] = inkex.BoundingBox.new_xywh(x, y, w, h)
                except ValueError:
                    # the output may contain empty lines!
                    pass
        return BB

    def bounding_box(self, elem):
        """get the bounding box of an SVG object
        If the bounding box is not easy to compute (typically, for a text element),
        the get_all_inkscape_bboxes is used to ask the external inkscape command for
        all bounding boxes. They are then kept in a dictionnary so that later calls
        to the method are faster.
        """

        # bounding boxes are kept in self.BB, indexed by the element's id
        # check
        k = elem.get_id()
        if self.BB:
            bb = self.BB.get(k, inkex.BoundingBox())
            if bb is not None:
                return bb
            else:
                self.abort(f"ERROR: cannot retrieve the bounding box for element with id '{k}'")

        # if self.BB isn't defined, try computing the bounding box normally
        bb = utils.bounding_box(elem, elem.getparent().composed_transform())
        if bb is not None:
            return bb
        else:
            # we only call get_all_inkscape_bboxes when this computation failed
            self.set_timer("get_bb")  # start timer
            self.message(">>>", _("calling external inkscape command to retrieve bounding boxes"), verbosity=4)
            self.BB = self.get_all_inkscape_bboxes()
            self.message(
                ">>>",
                _("running time for external inkscape command: {time:.0f}ms").format(time=self.get_timer("get_bb")),
                verbosity=4,
            )
            bb = self.BB.get(k, inkex.BoundingBox())
            return bb

    #############################
    # dealing with artifacts... #
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
            root.add(artifact_layer)  # insert last, ie at top
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
        if self.config["artifacts_overlay_opacity"] > 0:
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
            artifact_overlay = svg.getElementById(ARTIFACT_OVERLAY_GROUP_ID)
            if artifact_overlay is not None:
                artifact_overlay.getparent().remove(artifact_overlay)

    def clean_artifacts(self, force=False):
        """remove the artifact layer / group if it is empty
        If force is true, remove it even if it is not empty"""
        svg = self.svg

        artifact_layer = svg.getElementById(ARTIFACT_LAYER_ID)
        artifact_group = svg.getElementById(ARTIFACT_GROUP_ID)
        artifact_overlay = svg.getElementById(ARTIFACT_OVERLAY_GROUP_ID)

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

    def extract_non_artifacts(self):
        """look through the artifact layer and move all non-artifact outside"""
        artifact_layer = self.svg.getElementById(ARTIFACT_LAYER_ID)
        artifact_bg_layer = self.svg.getElementById(ARTIFACT_LAYER_ID)

        counter = 0
        for layer in [artifact_layer, artifact_bg_layer]:
            if layer is None:
                continue
            for elem in _iter_elements(
                layer,
                skip_groups=False,
                skip_artifacts=False,
            ):
                cl = elem.get("class")
                if cl and ARTIFACT_CLASS in cl:
                    continue
                counter += 1
                self.message(
                    "\t-",
                    _("object with id={id} was moved out of the artifact layer").format(id=elem.get_id()),
                    verbosity=2,
                )
                tr = elem.getparent().composed_transform()
                elem.getparent().remove(elem)
                elem.transform = tr @ elem.transform
                self.svg.add(elem)
            if counter > 0:
                self.message(
                    ngettext(
                        "{counter} object was moved out of the artifact layer",
                        "{counter} object was moved out of the artifact layer",
                        counter,
                    ).format(counter=counter),
                    verbosity=1,
                )

    def update_overlay(self, bb):
        if self.config["artifacts_overlay_opacity"] == 0:
            return
        rect = self.svg.getElementById(ARTIFACT_OVERLAY_ID)
        if rect is None:
            w = self.svg.unittouu(self.svg.viewport_width)
            h = self.svg.unittouu(self.svg.viewport_height)
            rect = inkex.Rectangle.new(0, 0, w, h)
            rect.set("id", ARTIFACT_OVERLAY_ID)
            rect.set("class", ARTIFACT_CLASS)
            rect.set_sensitive(False)
            rect.style = inkex.Style(
                {
                    "fill": f"url(#{ARTIFACT_OVERLAY_PATTERN_ID})",
                    "opacity": self.config["artifacts_overlay_opacity"] / 100,
                    "stroke": "none",
                    "stroke-width": "1px",
                }
            )

            g = inkex.Group(id=ARTIFACT_OVERLAY_GROUP_ID)
            g.set("class", ARTIFACT_CLASS)

            self.svg.root.insert(0, g)
            g.add(rect)

            # add a border for easy selection of overlay
            m = self.mm_to_svg(10)
            border = inkex.Rectangle.new(-m / 2, -m / 2, w + m, h + m)
            border.set("id", ARTIFACT_OVERLAY_BORDER_ID)
            border.set("class", ARTIFACT_CLASS)
            border.style = inkex.Style(
                {
                    "fill": "none",
                    "stroke": f"url(#{ARTIFACT_OVERLAY_PATTERN_ID})",
                    "stroke-width": m,
                }
            )
            g.add(border)

        border = self.svg.getElementById(ARTIFACT_OVERLAY_BORDER_ID)

        if bb is not None:
            bb = bb + rect.shape_box()
            rect.set("x", bb.left)
            rect.set("y", bb.top)
            rect.set("width", bb.width)
            rect.set("height", bb.height)

            assert border is not None
            m = self.mm_to_svg(10)
            border.set("x", bb.left - m / 2)
            border.set("y", bb.top - m / 2)
            border.set("width", bb.width + m)
            border.set("height", bb.height + m)

    def outline_bounding_box(self, level, elem, bb=None, msg=None, margin=1, **style):
        """outline the bounding box of elem
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

    def __new_artifact_bb(self, level, bb, id, msg=None, margin=1, **style):
        rect = self.svg.getElementById(id)
        if rect is None:
            margin = self.mm_to_svg(margin)
            x, y = bb.left, bb.top
            w, h = bb.width, bb.height
            rect = inkex.Rectangle.new(x - margin, y - margin, w + 2 * margin, h + 2 * margin)
            rect.set("id", id)
            rect.set("class", ARTIFACT_CLASS)
            rect.style = inkex.Style(
                {
                    "error-level": "-1",  # custom style attribute
                }
            )

        # add the message in the description
        if msg is not None:
            desc = rect.desc or ""
            desc += msg + "\n"
            rect.desc = desc

        if int(rect.style.get("error-level")) > level:
            # existing bounding box has higher error-level: keep existing style
            return

        rect.style["error-level"] = str(level)
        rect.style["fill"] = "none"
        rect.style["stroke-opacity"] = self.config["artifacts_opacity"] / 100
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
            assert False

        for k in style:
            rect.style[k.replace("_", "-")] = style[k]
        self.artifact_group.add(rect)

        # convert stroke-width to actual mm
        rect.style["stroke-width"] = self.mm_to_svg(rect.style["stroke-width"])

    def outline_arrow(self, level, elem, p=None, msg=None, margin=1, **style):
        if elem is None and p is None:
            self.abort("ERROR: method `outline_arrow` needs either an SVG element or an explicit point")

        if p is None:
            bb = self.bounding_box(elem)
            p = (bb.left, bb.bottom)

        x, y = p

        if elem is None:
            id = self.svg.get_unique_id("artifact_arrow")
        else:
            id = f"{ARTIFACT_CLASS}_arrow_{elem.get_id()}"

        self.__new_artifact_arrow(level, x, y, id, length=10, msg=msg, margin=margin, **style)

        if level > NOTE:
            self.update_overlay(inkex.BoundingBox())

    def __new_artifact_arrow(self, level, x, y, id, msg=None, length=10, margin=1, **style):
        """add an artifact arrow in the error layer
        elem is the element the arrow should be pointing to
        """
        arrow = self.svg.getElementById(id)
        if arrow is None:
            side = self.mm_to_svg(length)
            margin = self.mm_to_svg(margin)
            arrow = inkex.PathElement()
            arrow.set("id", id)
            arrow.set("class", ARTIFACT_CLASS)
            arrow.path = [Move(x - side, y + side), Line(x - margin, y + margin)]
            arrow.style = inkex.Style(
                {
                    "error-level": -1,  # custom style attribute
                }
            )

        # add the message in the description
        if msg is not None:
            desc = arrow.desc or ""
            desc += msg + "\n"
            arrow.desc = desc

        if int(arrow.style.get("error-level")) > level:
            # existing arrow has higher error-level: keep existing style
            return

        arrow.style["error-level"] = str(level)
        arrow.style["fill"] = "none"
        arrow.style["opacity"] = self.config["artifacts_opacity"] / 100
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
            assert False

        for k in style:
            arrow.style[k.replace("_", "-")] = style[k]
        self.artifact_group.add(arrow)

        # Add the artifact to the error group (inside the error layer)
        self.artifact_group.add(arrow)

        # convert stroke-width to actual mm
        arrow.style["stroke-width"] = self.mm_to_svg(arrow.style["stroke-width"])

    ###############################
    # misc initialisation methods #
    def _new_marker(self, id, color):
        """define an arrowhead marker for the arrow artifacts"""
        marker = inkex.Marker(
            id=id,
            orient="auto",  # orient='auto-start-reverse',
            markerWidth="3",
            markerHeight="3",
        )
        marker.set("class", ARTIFACT_CLASS)

        arrow = inkex.PathElement()
        arrow.set("class", ARTIFACT_CLASS)
        arrow.path = [Move(-3, 3), Line(0, 0), Line(-3, -3)]
        arrow.style = inkex.Style(
            {
                "stroke": color,
                "stroke-width": 1,
                "fill": "none",
                # "stroke-opacity": self.config["artifacts_opacity"]/100,
            }
        )
        marker.append(arrow)
        self.svg.defs.append(marker)


# vim: textwidth=120 foldmethod=indent foldlevel=0
