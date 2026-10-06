"""Parse HTML into a small tree and check it against WCAG 2.1 accessibility rules.

Only the Python standard library is used. The checks are static: they look at the
HTML source, not at how a browser renders it (so no colour-contrast or keyboard tests).
"""
from dataclasses import dataclass, asdict
from html.parser import HTMLParser

VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
             "meta", "param", "source", "track", "wbr"}
SKIP_TEXT_TAGS = {"script", "style"}
HEADING_TAGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}
NON_LABELLED_INPUT_TYPES = {"hidden", "submit", "reset", "button", "image"}


class Node:
    """One HTML element. `children` holds child Nodes and text strings in order."""

    def __init__(self, tag, attrs, line, parent=None):
        self.tag = tag
        self.attrs = {name: (value if value is not None else "") for name, value in attrs}
        self.line = line
        self.parent = parent
        self.children = []

    def get(self, name):
        return self.attrs.get(name)

    def iter(self):
        """Yield this node and every descendant in document order."""
        yield self
        for child in self.children:
            if isinstance(child, Node):
                yield from child.iter()

    def text(self):
        """Visible text inside the element; an image contributes its alt text."""
        parts = []
        for child in self.children:
            if isinstance(child, str):
                parts.append(child)
            elif child.tag == "img":
                parts.append(child.attrs.get("alt", ""))
            else:
                parts.append(child.text())
        return " ".join(" ".join(parts).split())

    def snippet(self, limit=80):
        attrs = " ".join(f'{k}="{v}"' for k, v in list(self.attrs.items())[:3])
        text = f"<{self.tag} {attrs}>" if attrs else f"<{self.tag}>"
        return text if len(text) <= limit else text[: limit - 3] + "..."


class TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#document", [], 0)
        self.current = self.root

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.getpos()[0], self.current)
        self.current.children.append(node)
        if tag not in VOID_TAGS:
            self.current = node

    def handle_startendtag(self, tag, attrs):  # e.g. <div/> or <br/>
        self.current.children.append(Node(tag, attrs, self.getpos()[0], self.current))

    def handle_endtag(self, tag):
        if tag in VOID_TAGS:
            return
        node = self.current
        while node is not None and node.tag != tag:
            node = node.parent
        if node is not None and node is not self.root:
            self.current = node.parent  # also closes any tags left open inside it

    def handle_data(self, data):
        if self.current.tag in SKIP_TEXT_TAGS or not data.strip():
            return
        self.current.children.append(data)


def parse_html(source):
    builder = TreeBuilder()
    builder.feed(source)
    builder.close()
    return builder.root


@dataclass
class Violation:
    rule: str
    wcag: str
    severity: str
    message: str
    line: int
    snippet: str

    def to_dict(self):
        return asdict(self)


# rule id -> (WCAG success criterion, severity, description)
RULES = {
    "html-lang": ("3.1.1", "error", "<html> must have a lang attribute"),
    "document-title": ("2.4.2", "error", "page must have a non-empty <title>"),
    "img-alt": ("1.1.1", "error", "<img> must have an alt attribute (empty alt marks it decorative)"),
    "input-label": ("3.3.2", "error", "form fields must have a label or accessible name"),
    "button-name": ("4.1.2", "error", "<button> must have text or an accessible name"),
    "link-name": ("2.4.4", "error", "links must have text or an accessible name"),
    "duplicate-id": ("4.1.1", "error", "id values must be unique in the page"),
    "heading-order": ("1.3.1", "warning", "heading levels should not skip (for example h1 to h3)"),
    "tabindex-positive": ("2.4.3", "warning", "avoid tabindex above 0; it breaks natural tab order"),
}


def _violation(rule, node, message):
    wcag, severity, _ = RULES[rule]
    return Violation(rule, wcag, severity, message, node.line, node.snippet())


def _has_accessible_name(node):
    for attr in ("aria-label", "aria-labelledby", "title"):
        if (node.get(attr) or "").strip():
            return True
    return bool(node.text())


def check_html_lang(root):
    for node in root.iter():
        if node.tag == "html":
            if not (node.get("lang") or "").strip():
                yield _violation("html-lang", node, "<html> has no lang attribute")
            return


def check_document_title(root):
    html = next((n for n in root.iter() if n.tag == "html"), None)
    if html is None:
        return  # a fragment without <html> cannot be judged
    title = next((n for n in html.iter() if n.tag == "title"), None)
    if title is None or not title.text():
        yield _violation("document-title", html, "page has no <title> or it is empty")


def check_img_alt(root):
    for node in root.iter():
        if node.tag == "img" and node.get("alt") is None:
            if (node.get("role") or "").lower() in ("presentation", "none"):
                continue
            yield _violation("img-alt", node, "image has no alt attribute")


def check_input_label(root):
    label_targets = {n.get("for") for n in root.iter() if n.tag == "label" and n.get("for")}
    for node in root.iter():
        if node.tag not in ("input", "select", "textarea"):
            continue
        if node.tag == "input" and (node.get("type") or "text").lower() in NON_LABELLED_INPUT_TYPES:
            continue
        wrapped = False
        parent = node.parent
        while parent is not None:
            if parent.tag == "label":
                wrapped = True
                break
            parent = parent.parent
        named = any((node.get(a) or "").strip() for a in ("aria-label", "aria-labelledby", "title"))
        if not (wrapped or named or (node.get("id") and node.get("id") in label_targets)):
            yield _violation("input-label", node, f"<{node.tag}> has no label")


def check_button_name(root):
    for node in root.iter():
        if node.tag == "button" and not _has_accessible_name(node):
            yield _violation("button-name", node, "button has no text or accessible name")


def check_link_name(root):
    for node in root.iter():
        if node.tag == "a" and node.get("href") is not None and not _has_accessible_name(node):
            yield _violation("link-name", node, "link has no text or accessible name")


def check_duplicate_id(root):
    seen = set()
    for node in root.iter():
        value = node.get("id")
        if not value:
            continue
        if value in seen:
            yield _violation("duplicate-id", node, f'id "{value}" is used more than once')
        seen.add(value)


def check_heading_order(root):
    previous = 0
    for node in root.iter():
        level = HEADING_TAGS.get(node.tag)
        if level is None:
            continue
        if previous and level > previous + 1:
            yield _violation("heading-order", node, f"heading jumps from h{previous} to h{level}")
        previous = level


def check_tabindex_positive(root):
    for node in root.iter():
        value = node.get("tabindex")
        if value is None:
            continue
        try:
            if int(value) > 0:
                yield _violation("tabindex-positive", node, f"tabindex={value} is greater than 0")
        except ValueError:
            continue


CHECKS = [check_html_lang, check_document_title, check_img_alt, check_input_label,
          check_button_name, check_link_name, check_duplicate_id, check_heading_order,
          check_tabindex_positive]


def check_source(source):
    """Return all violations in an HTML string, ordered by line number."""
    root = parse_html(source)
    found = [v for check in CHECKS for v in check(root)]
    return sorted(found, key=lambda v: (v.line, v.rule))
