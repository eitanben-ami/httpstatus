# httpstatus — HTTP Status Code Reference CLI

A zero-dependency Python CLI for looking up, searching, and reasoning about HTTP status codes. Built for developers debugging APIs, writing documentation, or hunting obscure 4xx/5xx codes.

## About

`httpstatus` is a pocket reference for HTTP status codes. It ships with the full IANA-registered HTTP Status Code Registry and lets you query it from the terminal in multiple ways:

- Look up a code by number and get its title, category, and description.
- Search by name or description text.
- List all codes in a category (informational, success, redirection, client error, server error).
- Group codes by their category for a structured overview.
- Exit non-zero when investigating a client or server error code, useful in scripts and CI gates.

It runs on the Python standard library only — no network calls, no third-party packages, no caching.

## Features

- **Full IANA registry** — every registered HTTP status code: 1xx through 5xx.
- **Look up by code** — `httpstatus 404` returns the canonical name and description.
- **Search by name** — `httpstatus --search not-found` hits multiple matching codes.
- **Search by description** — `httpstatus --search-description "not found"` finds codes whose description mentions a phrase.
- **Category filter** — `httpstatus --category error` lists all 4xx and 5xx codes.
- **Grouped output** — `httpstatus --group` prints codes organized by category.
- **All codes** — `httpstatus --all` dumps the full registry.
- **Output formats** — plain text (default) or JSON for scripting.
- **Check mode** — `httpstatus --check 500` exits 1 when the code is a client or server error, useful for API health gates.
- **Stdin mode** — pass `-` as the code argument to read codes from stdin, one per line.
- **Zero runtime dependencies** — only the Python standard library.

## Installation

```bash
pip install httpstatus
```

Or from source:

```bash
git clone https://github.com/eitanben-ami/httpstatus
cd httpstatus
pip install -e ".[dev]"
```

Requires Python 3.11+.

## Usage

### Look up a status code

```bash
httpstatus 404
# 404 Not Found
# The server cannot find the requested resource.
```

### Search by name

```bash
httpstatus --search not-found
# 404 Not Found — The server cannot find the requested resource.
#
# 410 Gone — The requested resource is no longer available and will not be available again.
```

### Search by description text

```bash
httpstatus --search-description "conflict"
# 409 Conflict — The request could not be completed due to a conflict with the current state of the resource.
# 422 Unprocessable Content — The server understands the content type and syntax, but cannot process the contained instructions.
```

### List codes in a category

```bash
httpstatus --category error
# 400 Bad Request
# 401 Unauthorized
# ...
# 500 Internal Server Error
# ...
```

Categories: `informational`, `success`, `redirection`, `client-error`, `server-error`, or `error` (client + server).

### Grouped overview

```bash
httpstatus --group
# === 1xx Informational ===
# 100 Continue
# 101 Switching Protocols
# ...
#
# === 4xx Client Error ===
# 400 Bad Request
# ...
```

### All codes

```bash
httpstatus --all
```

### Check mode (CI gate)

Exit non-zero when the code represents a client or server error:

```bash
httpstatus --check 200 && echo ok
# ok

httpstatus --check 503 && echo degraded || echo degraded
# degraded
```

### JSON output

```bash
httpstatus 404 --format json
# {"code": 404, "name": "Not Found", "category": "client-error", "description": "The server cannot find the requested resource."}
```

List and search commands also support `--format json`.

### Stdin mode

Read codes from stdin (one per line):

```bash
printf "200\n404\n500\n" | httpstatus -
# 200 OK
# 404 Not Found
# 500 Internal Server Error
```

Combine with `--check` to validate a list of response codes:

```bash
curl -s https://api.example.com/health | jq -r .status | httpstatus --check - && echo healthy
```

## Project structure

```text
httpstatus/
├── httpstatus.py      # Main module and CLI entrypoint
├── pyproject.toml     # Packaging, metadata, and dev dependencies
├── README.md          # This file
├── .gitignore
└── tests/
    └── test_httpstatus.py
```

## Contributing

Issues and pull requests are welcome. To contribute:

1. Fork the repository.
2. Create a feature branch (`git checkout -b my-feature`).
3. Make your changes and add or update tests as needed.
4. Run `pytest tests/` and `ruff check httpstatus.py` to keep the suite green and clean.
5. Open a pull request against `main`.

For bugs, include the HTTP status code you were looking up and the output you expected versus what you got.

## Source

Repository: [https://github.com/eitanben-ami/httpstatus](https://github.com/eitanben-ami/httpstatus)

## Tags

`http`, `status-codes`, `iana`, `cli`, `reference`, `developer-tools`, `python`, `api-debugging`
