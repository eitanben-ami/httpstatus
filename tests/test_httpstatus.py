"""Tests for httpstatus — HTTP status code reference CLI."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpstatus as h  # noqa: E402


# ---------------------------------------------------------------------------
# Registry / library helpers
# ---------------------------------------------------------------------------


def test_registry_contains_full_iana_set():
    codes = {s.code for s in h.REGISTRY}
    expected = {
        100, 101, 102, 103,
        200, 201, 202, 203, 204, 205, 206, 207, 208, 226,
        300, 301, 302, 303, 304, 305, 307, 308,
        400, 401, 402, 403, 404, 405, 406, 407, 408, 409,
        410, 411, 412, 413, 414, 415, 416, 417, 418, 421,
        422, 423, 424, 425, 426, 428, 429, 431, 434, 451,
        500, 501, 502, 503, 504, 505, 506, 507, 508, 510, 511,
    }
    assert codes == expected


def test_describe_known_code():
    s = h.describe(404)
    assert s is not None
    assert s.code == 404
    assert s.name == "Not Found"
    assert s.category == h.CAT_CLIENT_ERROR


def test_describe_unknown_code():
    assert h.describe(999) is None


def test_is_error_4xx():
    assert h.is_error(400) is True
    assert h.is_error(404) is True
    assert h.is_error(451) is True


def test_is_error_5xx():
    assert h.is_error(500) is True
    assert h.is_error(503) is True


def test_is_error_non_error():
    assert h.is_error(200) is False
    assert h.is_error(301) is False
    assert h.is_error(0) is False


def test_codes_in_category_client_error():
    items = h.codes_in_category("client-error")
    assert all(s.category == h.CAT_CLIENT_ERROR for s in items)
    assert 404 in {s.code for s in items}


def test_codes_in_category_error_aggregate():
    items = h.codes_in_category("error")
    assert all(s.category in (h.CAT_CLIENT_ERROR, h.CAT_SERVER_ERROR) for s in items)
    assert 404 in {s.code for s in items}
    assert 500 in {s.code for s in items}


def test_codes_in_category_unknown_returns_empty():
    assert h.codes_in_category("unicorn") == []


def test_search_by_name_exact():
    items = h.search_by_name("Not Found")
    assert len(items) == 1
    assert items[0].code == 404


def test_search_by_name_partial():
    items = h.search_by_name("Found")
    names = {s.name for s in items}
    assert "Not Found" in names
    assert "404" not in names  # names only, codes excluded


def test_search_by_name_case_insensitive():
    items = h.search_by_name("NOT FOUND")
    assert any(s.code == 404 for s in items)


def test_search_by_name_no_match():
    assert h.search_by_name("xyzzy") == []


def test_search_by_description_partial():
    items = h.search_by_description("teapot")
    assert any(s.code == 418 for s in items)


def test_search_by_description_conflict():
    items = h.search_by_description("conflict")
    codes = {s.code for s in items}
    # Both 409 Conflict and 422 mention conflicts in their descriptions.
    assert 409 in codes or 422 in codes


def test_search_by_description_empty_query_returns_nothing():
    assert h.search_by_description("") == []


# ---------------------------------------------------------------------------
# Output rendering
# ---------------------------------------------------------------------------


def test_render_plain_known_code():
    out = h.render_plain(200)
    assert out.startswith("200 OK")
    assert "The request has succeeded" in out


def test_render_plain_unknown_code():
    out = h.render_plain(999)
    assert "unknown HTTP status code" in out
    assert "999" in out


def test_render_plain_list_multiple():
    items = [h.describe(200), h.describe(404)]
    out = h.render_plain_list(items)
    assert "200 OK" in out
    assert "404 Not Found" in out


def test_render_plain_list_empty():
    assert h.render_plain_list([]) == "No matching status codes."


def test_render_json_result_known():
    payload = json.loads(h.render_json_result(404))
    assert payload["code"] == 404
    assert payload["name"] == "Not Found"
    assert payload["category"] == "client-error"
    assert "description" in payload


def test_render_json_result_unknown():
    payload = json.loads(h.render_json_result(999))
    assert payload["code"] == 999
    assert "error" in payload
    assert "name" not in payload


# ---------------------------------------------------------------------------
# CLI: positional lookup (capsys, no stdout monkeypatch)
# ---------------------------------------------------------------------------


def test_main_lookup_200(capsys):
    code = h.main(["200"])
    captured = capsys.readouterr()
    assert code == 0
    assert "200 OK" in captured.out
    assert "The request has succeeded" in captured.out


def test_main_lookup_404(capsys):
    code = h.main(["404"])
    captured = capsys.readouterr()
    assert code == 0
    assert "404 Not Found" in captured.out


def test_main_unknown_code_exit_0(capsys):
    code = h.main(["999"])
    captured = capsys.readouterr()
    assert code == 0
    assert "999" in captured.out
    assert "unknown" in captured.out.lower()


def test_main_missing_code_exit_2(capsys):
    code = h.main([])
    assert code == 2


def test_main_positional_invalid_code_exit_2(capsys):
    # Invalid token should exit 2 via the CLI error contract.
    code = h.main(["abc"])
    assert code == 2


def test_main_help_exit_0(capsys):
    code = h.main(["--help"])
    captured = capsys.readouterr()
    assert code == 0
    assert "HTTP status code reference and lookup" in captured.out


def test_main_version_exit_0(capsys):
    code = h.main(["--version"])
    captured = capsys.readouterr()
    assert code == 0
    assert "httpstatus 0.1.0" in captured.out


# ---------------------------------------------------------------------------
# CLI: --check mode
# ---------------------------------------------------------------------------


def test_main_check_success_exit_0(capsys):
    code = h.main(["200", "--check"])
    captured = capsys.readouterr()
    assert code == 0
    assert "200 OK" in captured.out


def test_main_check_client_error_exit_1(capsys):
    code = h.main(["404", "--check"])
    captured = capsys.readouterr()
    assert code == 1
    assert "404 Not Found" in captured.out


def test_main_check_server_error_exit_1(capsys):
    code = h.main(["503", "--check"])
    assert code == 1


# ---------------------------------------------------------------------------
# CLI: --search
# ---------------------------------------------------------------------------


def test_main_search_exact(capsys):
    code = h.main(["--search", "Not Found"])
    captured = capsys.readouterr()
    assert code == 0
    assert "404 Not Found" in captured.out


def test_main_search_partial(capsys):
    code = h.main(["--search", "Found"])
    captured = capsys.readouterr()
    assert code == 0
    assert "404 Not Found" in captured.out


def test_main_search_no_match(capsys):
    code = h.main(["--search", "xyzzy"])
    captured = capsys.readouterr()
    assert code == 0
    assert "No matching status codes" in captured.out


# ---------------------------------------------------------------------------
# CLI: --search-description
# ---------------------------------------------------------------------------


def test_main_search_description_teapot(capsys):
    code = h.main(["--search-description", "teapot"])
    captured = capsys.readouterr()
    assert code == 0
    assert "418" in captured.out
    assert "Teapot" in captured.out


# ---------------------------------------------------------------------------
# CLI: --category
# ---------------------------------------------------------------------------


def test_main_category_error_plain(capsys):
    code = h.main(["--category", "error"])
    captured = capsys.readouterr()
    assert code == 0
    assert "404 Not Found" in captured.out
    assert "500 Internal Server Error" in captured.out


def test_main_category_success_plain(capsys):
    code = h.main(["--category", "success"])
    captured = capsys.readouterr()
    assert code == 0
    assert "200 OK" in captured.out
    assert "404" not in captured.out


def test_main_category_unknown_plain(capsys):
    code = h.main(["--category", "unicorn"])
    captured = capsys.readouterr()
    assert code == 0
    assert "No matching status codes" in captured.out


def test_main_category_error_json(capsys):
    code = h.main(["--category", "error", "--format", "json"])
    captured = capsys.readouterr()
    assert code == 0
    data = json.loads(captured.out)
    names = {item["name"] for item in data}
    assert "Not Found" in names
    assert "Internal Server Error" in names


# ---------------------------------------------------------------------------
# CLI: --group
# ---------------------------------------------------------------------------


def test_main_group_plain(capsys):
    code = h.main(["--group"])
    captured = capsys.readouterr()
    assert code == 0
    assert "=== Informational" in captured.out
    assert "=== Client Error (client-error) ===" in captured.out
    assert "404 Not Found" in captured.out  # body lists "code name" pairs


def test_main_group_json(capsys):
    code = h.main(["--group", "--format", "json"])
    captured = capsys.readouterr()
    assert code == 0
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert any(item["code"] == 404 for item in data)


# ---------------------------------------------------------------------------
# CLI: --all
# ---------------------------------------------------------------------------


def test_main_all_plain(capsys):
    code = h.main(["--all"])
    captured = capsys.readouterr()
    assert code == 0
    assert "100 Continue" in captured.out
    assert "511 Network Authentication Required" in captured.out


def test_main_all_json(capsys):
    code = h.main(["--all", "--format", "json"])
    captured = capsys.readouterr()
    assert code == 0
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert len(data) == len(h.REGISTRY)


# ---------------------------------------------------------------------------
# CLI: stdin mode (main(["-"], stdin=...))
# ---------------------------------------------------------------------------


def test_main_stdin_single_code(capsys):
    code = h.main(["-"], stdin="200\n")
    captured = capsys.readouterr()
    assert code == 0
    assert "200 OK" in captured.out


def test_main_stdin_multiple_codes(capsys):
    code = h.main(["-"], stdin="200\n404\n500\n")
    captured = capsys.readouterr()
    assert code == 0
    assert "200 OK" in captured.out
    assert "404 Not Found" in captured.out
    assert "500 Internal Server Error" in captured.out


def test_main_stdin_check_error_exit_1(capsys):
    code = h.main(["-", "--check"], stdin="200\n500\n")
    captured = capsys.readouterr()
    assert code == 1
    assert "500 Internal Server Error" in captured.out


def test_main_stdin_empty_lines_ignored(capsys):
    code = h.main(["-"], stdin="\n\n200\n\n")
    captured = capsys.readouterr()
    assert code == 0
    assert "200 OK" in captured.out


# ---------------------------------------------------------------------------
# CLI: --check with stdin (positive + negative gating)
# ---------------------------------------------------------------------------


def test_main_stdin_check_all_ok_exit_0(capsys):
    code = h.main(["-", "--check"], stdin="200\n301\n")
    assert code == 0


def test_main_stdin_check_mixed_exit_1(capsys):
    code = h.main(["-", "--check"], stdin="200\n404\n")
    assert code == 1


# ---------------------------------------------------------------------------
# CLI: invalid stdin token exits 2
# ---------------------------------------------------------------------------


def test_main_stdin_invalid_code_exit_2(capsys):
    code = h.main(["-"], stdin="abc\n")
    assert code == 2