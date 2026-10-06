import json

from a11ylint.cli import main

GOOD = '<html lang="en"><head><title>T</title></head><body><h1>Hi</h1></body></html>'
BAD = '<html lang="en"><head><title>T</title></head><body><img src="a.png"></body></html>'
WARN_ONLY = '<html lang="en"><head><title>T</title></head><body><h1>A</h1><h3>B</h3></body></html>'


def write(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return str(path)


def test_clean_file_exits_zero(tmp_path, capsys):
    assert main([write(tmp_path, "a.html", GOOD)]) == 0
    assert "0 error(s), 0 warning(s)" in capsys.readouterr().out


def test_file_with_errors_exits_one(tmp_path, capsys):
    assert main([write(tmp_path, "a.html", BAD)]) == 1
    assert "img-alt" in capsys.readouterr().out


def test_fail_on_never_always_exits_zero(tmp_path):
    assert main([write(tmp_path, "a.html", BAD), "--fail-on", "never"]) == 0


def test_warnings_only_pass_by_default_but_fail_with_fail_on_warning(tmp_path):
    path = write(tmp_path, "a.html", WARN_ONLY)
    assert main([path]) == 0
    assert main([path, "--fail-on", "warning"]) == 1


def test_json_output_is_valid_and_has_counts(tmp_path, capsys):
    main([write(tmp_path, "a.html", BAD), "--format", "json", "--fail-on", "never"])
    data = json.loads(capsys.readouterr().out)
    assert data["errors"] == 1 and data["files_checked"] == 1
    assert data["files"][0]["violations"][0]["rule"] == "img-alt"


def test_folder_is_searched_recursively_for_html_files(tmp_path, capsys):
    (tmp_path / "sub").mkdir()
    write(tmp_path, "a.html", GOOD)
    write(tmp_path / "sub", "b.htm", GOOD)
    write(tmp_path, "notes.txt", "ignore me")
    assert main([str(tmp_path)]) == 0
    assert "2 file(s) checked" in capsys.readouterr().out


def test_missing_path_exits_two(tmp_path, capsys):
    assert main([str(tmp_path / "nope.html")]) == 2
    assert "path not found" in capsys.readouterr().err


def test_no_arguments_exits_two(capsys):
    assert main([]) == 2


def test_folder_without_html_exits_two(tmp_path):
    assert main([str(tmp_path)]) == 2


def test_list_rules_prints_every_rule(capsys):
    assert main(["--list-rules"]) == 0
    out = capsys.readouterr().out
    assert "img-alt" in out and "heading-order" in out
