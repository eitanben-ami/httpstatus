"""
httpstatus — HTTP status code reference CLI.

Zero-dependency lookup for IANA-registered HTTP status codes.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import NamedTuple

# ---------------------------------------------------------------------------
# Status code registry
# ---------------------------------------------------------------------------

CAT_INFORMATIONAL = "informational"
CAT_SUCCESS = "success"
CAT_REDIRECTION = "redirection"
CAT_CLIENT_ERROR = "client-error"
CAT_SERVER_ERROR = "server-error"

CAT_DISPLAY: dict[str, str] = {
    CAT_INFORMATIONAL: "Informational",
    CAT_SUCCESS: "Success",
    CAT_REDIRECTION: "Redirection",
    CAT_CLIENT_ERROR: "Client Error",
    CAT_SERVER_ERROR: "Server Error",
}


class StatusCode(NamedTuple):
    code: int
    name: str
    category: str
    description: str


REGISTRY: list[StatusCode] = [
    # Informational (1xx)
    StatusCode(100, "Continue", CAT_INFORMATIONAL, "The server has received the request headers and the client should proceed to send the request body."),
    StatusCode(101, "Switching Protocols", CAT_INFORMATIONAL, "The server is switching protocols as requested by the client via the Upgrade header."),
    StatusCode(102, "Processing", CAT_INFORMATIONAL, "The server has received and is processing the request, but no response is available yet (WebDAV)."),
    StatusCode(103, "Early Hints", CAT_INFORMATIONAL, "The server is sending early hints to preload resources while the response is still being prepared."),
    # Success (2xx)
    StatusCode(200, "OK", CAT_SUCCESS, "The request has succeeded. The meaning of the success depends on the HTTP method."),
    StatusCode(201, "Created", CAT_SUCCESS, "The request has been fulfilled and has resulted in one or more new resources being created."),
    StatusCode(202, "Accepted", CAT_SUCCESS, "The request has been accepted for processing, but the processing has not been completed."),
    StatusCode(203, "Non-Authoritative Information", CAT_SUCCESS, "The request was successful but the enclosed payload has been modified from that of the origin server's response."),
    StatusCode(204, "No Content", CAT_SUCCESS, "The server has successfully fulfilled the request and there is no additional content to send in the response payload body."),
    StatusCode(205, "Reset Content", CAT_SUCCESS, "The server has fulfilled the request and desires that the client reset the document view that caused the request to be sent."),
    StatusCode(206, "Partial Content", CAT_SUCCESS, "The server is delivering only part of the resource due to a range header sent by the client."),
    StatusCode(207, "Multi-Status", CAT_SUCCESS, "The message body contains a number of separate response codes for a batch request (WebDAV)."),
    StatusCode(208, "Already Reported", CAT_SUCCESS, "The members of a DAV binding have already been enumerated in a preceding part of the multi-status response (WebDAV)."),
    StatusCode(226, "IM Used", CAT_SUCCESS, "The server has fulfilled a GET request for the resource, and the response is a representation of the result of one or more instance-manipulations applied to the current instance."),
    # Redirection (3xx)
    StatusCode(300, "Multiple Choices", CAT_REDIRECTION, "The request has more than one possible response. The user agent or user should choose one."),
    StatusCode(301, "Moved Permanently", CAT_REDIRECTION, "The requested resource has been assigned a new permanent URI and any future references to this resource should use one of the returned URIs."),
    StatusCode(302, "Found", CAT_REDIRECTION, "The requested resource resides temporarily under a different URI."),
    StatusCode(303, "See Other", CAT_REDIRECTION, "The server is redirecting the user agent to a different resource as indicated by a URI in the Location header field."),
    StatusCode(304, "Not Modified", CAT_REDIRECTION, "A conditional GET or HEAD request has been received and would have resulted in a 200 OK response if the condition had not been met."),
    StatusCode(305, "Use Proxy", CAT_REDIRECTION, "The requested resource must be accessed through the proxy given by the Location field (deprecated)."),
    StatusCode(307, "Temporary Redirect", CAT_REDIRECTION, "The requested resource resides temporarily under a different URI and the user agent must not change the request method."),
    StatusCode(308, "Permanent Redirect", CAT_REDIRECTION, "The requested resource has been assigned a new permanent URI and any future references to this resource should use one of the returned URIs. The method must not change."),
    # Client Error (4xx)
    StatusCode(400, "Bad Request", CAT_CLIENT_ERROR, "The server cannot or will not process the request due to an apparent client error."),
    StatusCode(401, "Unauthorized", CAT_CLIENT_ERROR, "The request has not been applied because it lacks valid authentication credentials for the target resource."),
    StatusCode(402, "Payment Required", CAT_CLIENT_ERROR, "Reserved for future use. Originally intended for digital payment schemes."),
    StatusCode(403, "Forbidden", CAT_CLIENT_ERROR, "The server understood the request but refuses to authorize it."),
    StatusCode(404, "Not Found", CAT_CLIENT_ERROR, "The server cannot find the requested resource. In an API, this may mean the endpoint exists but the resource does not."),
    StatusCode(405, "Method Not Allowed", CAT_CLIENT_ERROR, "The method received in the request-line is known by the origin server but not supported by the target resource."),
    StatusCode(406, "Not Acceptable", CAT_CLIENT_ERROR, "The server cannot produce a response matching the list of acceptable values defined in the request's proactive negotiation headers."),
    StatusCode(407, "Proxy Authentication Required", CAT_CLIENT_ERROR, "The client must first authenticate itself with the proxy."),
    StatusCode(408, "Request Timeout", CAT_CLIENT_ERROR, "The server did not receive a complete request message within the time it was prepared to wait."),
    StatusCode(409, "Conflict", CAT_CLIENT_ERROR, "The request could not be completed due to a conflict with the current state of the resource."),
    StatusCode(410, "Gone", CAT_CLIENT_ERROR, "The requested resource is no longer available and will not be available again. This condition is expected to be permanent."),
    StatusCode(411, "Length Required", CAT_CLIENT_ERROR, "The server refuses to accept the request without a defined Content-Length header."),
    StatusCode(412, "Precondition Failed", CAT_CLIENT_ERROR, "One or more conditions given in the request header fields evaluated to false when tested on the server."),
    StatusCode(413, "Payload Too Large", CAT_CLIENT_ERROR, "The server is refusing to process a request because the request payload is larger than the server is willing or able to process."),
    StatusCode(414, "URI Too Long", CAT_CLIENT_ERROR, "The server is refusing to service the request because the request-target is longer than the server is willing to interpret."),
    StatusCode(415, "Unsupported Media Type", CAT_CLIENT_ERROR, "The origin server is refusing to service the request because the payload is in a format not supported by the target resource."),
    StatusCode(416, "Range Not Satisfiable", CAT_CLIENT_ERROR, "None of the ranges in the request's Range header field overlap the current extent of the selected resource."),
    StatusCode(417, "Expectation Failed", CAT_CLIENT_ERROR, "The expectation given in the request's Expect header field could not be met by at least one of the inbound servers."),
    StatusCode(418, "I'm a Teapot", CAT_CLIENT_ERROR, "Any attempt to brew coffee with a teapot should result in the error code 418 I'm a Teapot."),
    StatusCode(421, "Misdirected Request", CAT_CLIENT_ERROR, "The request was directed at a server that is not able to produce a response."),
    StatusCode(422, "Unprocessable Content", CAT_CLIENT_ERROR, "The server understands the content type and syntax, but cannot process the contained instructions."),
    StatusCode(423, "Locked", CAT_CLIENT_ERROR, "The source or destination resource of a method is locked (WebDAV)."),
    StatusCode(424, "Failed Dependency", CAT_CLIENT_ERROR, "The method could not be performed on the resource because the requested action depended on another action that failed (WebDAV)."),
    StatusCode(425, "Too Early", CAT_CLIENT_ERROR, "The server is unwilling to risk processing a request that might be replayed."),
    StatusCode(426, "Upgrade Required", CAT_CLIENT_ERROR, "The server refuses to perform the request using the current protocol but might be willing to do so after the client upgrades to a different protocol."),
    StatusCode(428, "Precondition Required", CAT_CLIENT_ERROR, "The origin server requires the request to be conditional."),
    StatusCode(429, "Too Many Requests", CAT_CLIENT_ERROR, "The user has sent too many requests in a given amount of time ('rate limiting')."),
    StatusCode(431, "Request Header Fields Too Large", CAT_CLIENT_ERROR, "The server is unwilling to process the request because its header fields are too large."),
    StatusCode(434, "Request Entity Too Large", CAT_CLIENT_ERROR, "The server is refusing to process a request because the request entity is larger than the server is willing or able to process."),
    StatusCode(451, "Unavailable For Legal Reasons", CAT_CLIENT_ERROR, "The server is denying access to the resource as a consequence of a legal demand."),
    # Server Error (5xx)
    StatusCode(500, "Internal Server Error", CAT_SERVER_ERROR, "The server encountered an unexpected condition that prevented it from fulfilling the request."),
    StatusCode(501, "Not Implemented", CAT_SERVER_ERROR, "The server does not support the functionality required to fulfill the request."),
    StatusCode(502, "Bad Gateway", CAT_SERVER_ERROR, "The server, while acting as a gateway or proxy, received an invalid response from an inbound server."),
    StatusCode(503, "Service Unavailable", CAT_SERVER_ERROR, "The server is currently unable to handle the request due to a temporary overload or scheduled maintenance."),
    StatusCode(504, "Gateway Timeout", CAT_SERVER_ERROR, "The server, while acting as a gateway or proxy, did not receive a timely response from an upstream server."),
    StatusCode(505, "HTTP Version Not Supported", CAT_SERVER_ERROR, "The server does not support, or refuses to support, the major version of HTTP that was used in the request message."),
    StatusCode(506, "Variant Also Negotiates", CAT_SERVER_ERROR, "The server has an internal configuration error: the chosen variant is configured to engage in transparent content negotiation itself."),
    StatusCode(507, "Insufficient Storage", CAT_SERVER_ERROR, "The method could not be performed on the resource because the server is unable to store the representation needed to complete the request (WebDAV)."),
    StatusCode(508, "Loop Detected", CAT_SERVER_ERROR, "The server terminated an operation because it encountered an infinite loop while processing a request with 'Depth: infinity' (WebDAV)."),
    StatusCode(510, "Not Extended", CAT_SERVER_ERROR, "The policy for accessing the resource requires use of the Extension field in the request."),
    StatusCode(511, "Network Authentication Required", CAT_SERVER_ERROR, "The client needs to authenticate to gain network access."),
]


def _by_code() -> dict[int, StatusCode]:
    return {s.code: s for s in REGISTRY}


BY_CODE: dict[int, StatusCode] = _by_code()


def describe(code: int) -> StatusCode | None:
    """Return the status code record for *code*, or None if unknown."""
    return BY_CODE.get(code)


def codes_in_category(category: str) -> list[StatusCode]:
    """Return all known status codes belonging to *category*."""
    cat = category.lower()
    if cat == "error":
        return [s for s in REGISTRY if s.category in (CAT_CLIENT_ERROR, CAT_SERVER_ERROR)]
    return [s for s in REGISTRY if s.category == cat]


def search_by_name(query: str) -> list[StatusCode]:
    """Return status codes whose canonical name contains *query* (case-insensitive)."""
    needle = query.lower()
    return [s for s in REGISTRY if needle in s.name.lower()]


def search_by_description(query: str) -> list[StatusCode]:
    """Return status codes whose description contains *query* (case-insensitive).

    Empty queries return no results.
    """
    if not query:
        return []
    needle = query.lower()
    return [s for s in REGISTRY if needle in s.description.lower()]


def is_error(code: int) -> bool:
    """True when *code* is a client error (4xx) or server error (5xx)."""
    return code >= 400


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def render_plain(code: int) -> str:
    s = describe(code)
    if s is None:
        return f"{code} — unknown HTTP status code"
    return f"{s.code} {s.name}\n{s.description}"


def render_plain_list(items: list[StatusCode]) -> str:
    if not items:
        return "No matching status codes."
    lines: list[str] = []
    for s in items:
        lines.append(f"{s.code} {s.name} — {s.description}")
    return "\n".join(lines)


def render_grouped() -> str:
    order = [
        CAT_INFORMATIONAL,
        CAT_SUCCESS,
        CAT_REDIRECTION,
        CAT_CLIENT_ERROR,
        CAT_SERVER_ERROR,
    ]
    blocks: list[str] = []
    for cat in order:
        items = codes_in_category(cat)
        prefix = f"=== {CAT_DISPLAY[cat]} ({cat}) ==="
        body = "\n".join(f"{s.code} {s.name}" for s in items)
        blocks.append(f"{prefix}\n{body}")
    return "\n\n".join(blocks)


def render_all() -> str:
    return "\n".join(f"{s.code} {s.name} — {s.description}" for s in REGISTRY)


def render_json_result(code: int) -> str:
    s = describe(code)
    if s is None:
        payload = {"code": code, "error": "unknown HTTP status code"}
    else:
        payload = {
            "code": s.code,
            "name": s.name,
            "category": s.category,
            "description": s.description,
        }
    return json.dumps(payload, ensure_ascii=False)


def render_json_list(items: list[StatusCode]) -> str:
    payload = [
        {"code": s.code, "name": s.name, "category": s.category, "description": s.description}
        for s in items
    ]
    return json.dumps(payload, ensure_ascii=False)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="httpstatus",
        description="HTTP status code reference and lookup.",
    )
    parser.add_argument(
        "code",
        nargs="?",
        default=None,
        help="HTTP status code to look up, or `-` to read codes from stdin.",
    )
    parser.add_argument(
        "--search",
        "-s",
        default=None,
        help="Search status codes by canonical name.",
    )
    parser.add_argument(
        "--search-description",
        default=None,
        help="Search status codes by description text.",
    )
    parser.add_argument(
        "--category",
        "-c",
        default=None,
        help="List all codes in a category.",
    )
    parser.add_argument(
        "--group",
        action="store_true",
        default=False,
        help="Print all codes grouped by category.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        default=False,
        help="Print every registered status code.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        default=False,
        help="Exit non-zero when the code is a client or server error.",
    )
    parser.add_argument(
        "--format",
        choices=["plain", "json"],
        default="plain",
        help="Output format (default: plain).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="httpstatus 0.1.0",
    )
    return parser


class _CLIError(Exception):
    """Raised by internal helpers to signal an error exit without sys.exit()."""

    def __init__(self, code: int, message: str = ""):
        self.code = code
        self.message = message


def main(argv: list[str] | None = None, stdin: str | None = None) -> int:
    parser = build_parser()
    args: argparse.Namespace

    # Handle stdin injection for tests without triggering argparse parse errors
    # on the positional `code` when `main([])` is called outside tests.
    if stdin is not None and (argv is None or argv == []):
        argv = ["-"]

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if exc.code is not None else 1

    fmt = args.format

    # Mode detection: only one primary mode at a time.
    if args.group:
        text = render_grouped()
        if fmt == "json":
            items = [s for s in REGISTRY]
            text = render_json_list(items)
        return _emit(text)

    if args.all:
        if fmt == "json":
            text = render_json_list(list(REGISTRY))
        else:
            text = render_all()
        return _emit(text)

    if args.category:
        items = codes_in_category(args.category)
        if fmt == "json":
            text = render_json_list(items)
        else:
            text = render_plain_list(items)
        return _emit(text)

    if args.search:
        items = search_by_name(args.search)
        if fmt == "json":
            text = render_json_list(items)
        else:
            text = render_plain_list(items)
        return _emit(text)

    if args.search_description:
        items = search_by_description(args.search_description)
        if fmt == "json":
            text = render_json_list(items)
        else:
            text = render_plain_list(items)
        return _emit(text)

    # Single code lookup (positional or stdin).
    code_arg = args.code
    if code_arg == "-":
        try:
            codes = _read_stdin_codes(stdin)
        except _CLIError as exc:
            if exc.message:
                print(exc.message, file=sys.stderr)
            return exc.code
    elif code_arg is None:
        print("httpstatus: error: the following arguments are required: code", file=sys.stderr)
        return 2
    else:
        try:
            codes = _parse_code_arg(code_arg)
        except _CLIError as exc:
            if exc.message:
                print(exc.message, file=sys.stderr)
            return exc.code

    if fmt == "json":
        lines: list[str] = []
        for code in codes:
            lines.append(render_json_result(code))
        return _emit("\n".join(lines))

    lines: list[str] = []
    for code in codes:
        lines.append(render_plain(code))
    text = "\n".join(lines)

    if args.check:
        # --check exits non-zero when ANY code is a client/server error.
        if any(is_error(c) for c in codes):
            return _emit(text + "\n") or 1
        return _emit(text + "\n") or 0

    return _emit(text + "\n") or 0


def _read_stdin_codes(stdin: str | None) -> list[int]:
    if stdin is None:
        payload = sys.stdin.read()
    else:
        payload = stdin
    codes: list[int] = []
    for line in payload.splitlines():
        token = line.strip()
        if not token:
            continue
        try:
            codes.append(int(token))
        except ValueError:
            raise _CLIError(2, f"httpstatus: invalid status code: {token!r}")
    return codes


def _parse_code_arg(raw: str) -> list[int]:
    if raw == "-":
        return _read_stdin_codes(None)
    try:
        return [int(raw.strip())]
    except ValueError:
        raise _CLIError(2, f"httpstatus: invalid status code: {raw.strip()!r}")


def _emit(text: str) -> int:
    """Write *text* to stdout and return 0."""
    print(text, end="")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except _CLIError as exc:
        if exc.message:
            print(exc.message, file=sys.stderr)
        raise SystemExit(exc.code)
