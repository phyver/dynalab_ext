import inkex

# Here is a list of relevant inkex classes for SVG elements
#
#  - inkex.Group
#  -    -> inkex.Layer          NOTE: instance of inkex.Group
#  -    -> inkex.ClipPath       NOTE: should only appear in <defs>
#  -    -> inkex.Symbol         NOTE: should only appear in <defs>
#  - inkex.Use          NOTE: inkscape's "clones"
#  - inkex.Image
#  - inkex.TextElement  NOTE: they can contain an inkex.TextPath referencing a
#                       path for text along path objects
#  - inkex.Ellipse
#  - inkex.Circle
#  - inkex.Rectangle
#  - inkex.Line         NOTE: inkscape uses PathElement instead
#  - inkex.Polyline     NOTE: inkscape uses PathElement instead
#  - inkex.Polygon      NOTE: inkscape uses PathElement instead
#  - inkex.PathElement
#


def is_path(elem, strict=False):
    if isinstance(elem, inkex.PathElement):
        return True

    if not strict and isinstance(
        elem, (inkex.Line, inkex.Polyline, inkex.Polygon, inkex.Rectangle, inkex.Ellipse, inkex.Circle)
    ):
        return True

    return False


def bounding_box(elem, transform):
    if is_path(elem) or isinstance(elem, inkex.Image):
        return elem.bounding_box(transform=transform)

    if isinstance(elem, inkex.TextElement):
        return None

    if isinstance(elem, inkex.Use):
        return bounding_box(elem.href, transform @ elem.transform)

    if isinstance(elem, inkex.Group):  # also works for layers
        # return elem.bounding_box(transform=transform)
        return None


def effects(elem):
    E = []  # list of effects

    if elem.get("inkscape:path-effect") is not None:
        E.append("path-effect")

    if elem.attrib.get("mask", "none") != "none":
        E.append("mask")
    if elem.attrib.get("clip-path", "none") != "none":
        E.append("clip-path")
    if elem.attrib.get("filter", "none") != "none":
        E.append("filter")

    # NOTE: apparently, some style attribute can end up in 2 places: as an
    # attribute of the element, or as a field in the style attribute.
    # We check both, to make sure we don't miss an effect.
    style = inkex.Style(elem.attrib.get("style", ""))
    attrs = elem.attrib

    dash1 = attrs.get("stroke-dasharray", "none")
    dash2 = style.get("stroke-dasharray", "none")
    if dash1 != "none" or dash2 != "none":
        E.append("stroke-dasharray")

    fill1 = attrs.get("fill", "")
    fill2 = style.get("fill", "")
    if fill1.startswith("url(#") or fill2.startswith("url(#"):
        E.append("url-fill")

    stroke1 = attrs.get("fill", "")
    stroke2 = style.get("stroke", "")
    if stroke1.startswith("url(#") or stroke2.startswith("url(#"):
        E.append("url-stroke")

    return E


def get_clone_reference_element(elem):
    if not isinstance(elem, inkex.Use):
        return elem
    else:
        return get_clone_reference_element(elem.href)
