# a11y-lint

A command-line tool, written in Python, that checks HTML files for common web accessibility
problems. It parses the HTML into a small tree, runs 9 rules mapped to WCAG 2.1 success
criteria, and reports every problem with its line number as plain text or JSON.

It uses only the Python standard library, so there is nothing to install to run it.

> **Scope:** these are static checks on the HTML source, covering a subset of WCAG 2.1.
> They do not test colour contrast, keyboard use or content that scripts add later.
> For a full audit, use a browser-based tool such as axe-core as well.

## Usage

```bash
python -m a11ylint samples/bad.html          # check one file
python -m a11ylint site/                     # check every .html / .htm file in a folder
python -m a11ylint site/ --format json       # machine-readable output
python -m a11ylint site/ --fail-on warning   # exit 1 on warnings as well as errors
python -m a11ylint --list-rules              # show all rules
```

Exit codes: `0` clean (or only issues below the `--fail-on` level), `1` problems found,
`2` bad usage (missing path, no HTML files). This makes it easy to fail a CI build.

Example output for `samples/bad.html`:

```
samples/bad.html:7: error img-alt (WCAG 1.1.1) image has no alt attribute
    <img src="logo.png">
samples/bad.html:8: error input-label (WCAG 3.3.2) <input> has no label
    <input type="text" name="email">
...
1 file(s) checked: 8 error(s), 2 warning(s)
```

## Rules

| Rule | WCAG | Severity | Checks that |
|---|---|---|---|
| `html-lang` | 3.1.1 | error | `<html>` has a `lang` attribute |
| `document-title` | 2.4.2 | error | the page has a non-empty `<title>` |
| `img-alt` | 1.1.1 | error | every `<img>` has `alt` (empty `alt` marks it decorative) |
| `input-label` | 3.3.2 | error | inputs, selects and textareas have a label or accessible name |
| `button-name` | 4.1.2 | error | buttons have text or an accessible name |
| `link-name` | 2.4.4 | error | links have text or an accessible name |
| `duplicate-id` | 4.1.1 | error | `id` values are unique |
| `heading-order` | 1.3.1 | warning | heading levels do not skip (h1 to h3) |
| `tabindex-positive` | 2.4.3 | warning | no `tabindex` above 0 |

## How it works

1. `TreeBuilder` (a subclass of `html.parser.HTMLParser`) turns the source into a tree of `Node`
   objects. It copes with unclosed tags and ignores text inside `<script>` and `<style>`.
2. Each rule is a small function that walks the tree and yields `Violation` objects.
3. `check_source` runs every rule and sorts the results by line number.
4. `report.py` formats the results as text or JSON, and `cli.py` handles arguments and exit codes.

## Run the tests

```bash
python -m venv .venv
.venv\Scripts\activate          # Mac/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

A GitHub Actions workflow runs the same tests on every push.

## Project layout

```
a11ylint/checker.py   HTML tree builder + the 9 rules
a11ylint/report.py    text and JSON output
a11ylint/cli.py       command-line interface
samples/              a clean page and a page with problems
tests/                pytest tests
```

## License

MIT
