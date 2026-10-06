from a11ylint.checker import check_source, parse_html

PAGE = '<html lang="en"><head><title>T</title></head><body>{}</body></html>'


def rules(html):
    return [v.rule for v in check_source(html)]


def body(snippet):
    return rules(PAGE.format(snippet))


def test_clean_page_has_no_violations():
    assert body('<h1>Hi</h1><a href="/x">Go</a>') == []


def test_missing_lang_is_reported():
    html = "<html><head><title>T</title></head><body></body></html>"
    assert rules(html) == ["html-lang"]


def test_missing_or_empty_title_is_reported():
    assert rules('<html lang="en"><head></head><body></body></html>') == ["document-title"]
    assert rules('<html lang="en"><head><title> </title></head></html>') == ["document-title"]


def test_fragment_without_html_tag_skips_page_level_rules():
    assert rules("<p>just a fragment</p>") == []


def test_image_without_alt_is_reported():
    assert body('<img src="a.png">') == ["img-alt"]


def test_empty_alt_and_presentation_role_are_allowed():
    assert body('<img src="a.png" alt="">') == []
    assert body('<img src="a.png" role="presentation">') == []


def test_input_without_label_is_reported():
    assert body('<input type="text">') == ["input-label"]


def test_input_with_label_for_wrapping_label_or_aria_label_is_fine():
    assert body('<label for="a">A</label><input id="a">') == []
    assert body("<label>A <input></label>") == []
    assert body('<input aria-label="Search">') == []


def test_hidden_and_submit_inputs_need_no_label():
    assert body('<input type="hidden"><input type="submit" value="Go">') == []


def test_textarea_and_select_need_labels():
    assert body("<textarea></textarea><select></select>") == ["input-label", "input-label"]


def test_button_without_name_is_reported():
    assert body("<button></button>") == ["button-name"]
    assert body('<button><img src="x.png"></button>') == ["button-name", "img-alt"]


def test_button_with_text_or_aria_label_is_fine():
    assert body("<button>Save</button>") == []
    assert body('<button aria-label="Close"></button>') == []


def test_link_without_name_is_reported():
    assert body('<a href="/x"></a>') == ["link-name"]


def test_link_with_image_alt_is_fine_and_anchor_without_href_is_ignored():
    assert body('<a href="/x"><img src="a.png" alt="Home"></a>') == []
    assert body('<a name="top"></a>') == []


def test_skipped_heading_level_is_reported():
    assert body("<h1>A</h1><h3>B</h3>") == ["heading-order"]


def test_sequential_and_going_back_up_headings_are_fine():
    assert body("<h1>A</h1><h2>B</h2><h3>C</h3><h2>D</h2>") == []


def test_duplicate_id_is_reported_once_per_extra_use():
    assert body('<p id="a"></p><p id="a"></p><p id="a"></p>') == ["duplicate-id", "duplicate-id"]


def test_positive_tabindex_is_a_warning():
    found = check_source(PAGE.format('<div tabindex="2"></div>'))
    assert [(v.rule, v.severity) for v in found] == [("tabindex-positive", "warning")]


def test_zero_negative_and_invalid_tabindex_are_fine():
    assert body('<div tabindex="0"></div><div tabindex="-1"></div><div tabindex="x"></div>') == []


def test_unclosed_tags_do_not_crash():
    assert body("<p>one<p>two<div><span>three") == []


def test_script_text_is_not_counted_as_button_text():
    assert body("<button><script>var x = 1;</script></button>") == ["button-name"]


def test_violation_reports_line_number_and_wcag_criterion():
    html = '<html lang="en">\n<head><title>T</title></head>\n<body>\n<img src="a.png">\n</body></html>'
    (violation,) = check_source(html)
    assert (violation.rule, violation.line, violation.wcag) == ("img-alt", 4, "1.1.1")


def test_parse_builds_nested_tree():
    root = parse_html("<div><p>Hello <b>there</b></p></div>")
    assert root.children[0].tag == "div"
    assert root.children[0].children[0].text() == "Hello there"
