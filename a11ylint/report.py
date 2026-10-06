"""Turn results into text or JSON. `results` is a list of (path, [Violation])."""
import json


def counts(results):
    errors = sum(1 for _, vs in results for v in vs if v.severity == "error")
    warnings = sum(1 for _, vs in results for v in vs if v.severity == "warning")
    return errors, warnings


def format_text(results):
    lines = []
    for path, violations in results:
        for v in violations:
            lines.append(f"{path}:{v.line}: {v.severity} {v.rule} (WCAG {v.wcag}) {v.message}")
            lines.append(f"    {v.snippet}")
    errors, warnings = counts(results)
    lines.append(f"{len(results)} file(s) checked: {errors} error(s), {warnings} warning(s)")
    return "\n".join(lines)


def format_json(results):
    errors, warnings = counts(results)
    payload = {
        "files_checked": len(results),
        "errors": errors,
        "warnings": warnings,
        "files": [{"path": str(path), "violations": [v.to_dict() for v in vs]}
                  for path, vs in results],
    }
    return json.dumps(payload, indent=2)
