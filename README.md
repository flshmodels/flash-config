# Flash Config

[![Tests](https://github.com/flshmodels/flash-config/actions/workflows/test.yml/badge.svg)](https://github.com/flshmodels/flash-config/actions/workflows/test.yml)

Check an item catalog before it reaches your game. Flash Config reads CSV or JSON, catches common data mistakes, and writes a frozen Luau table you can use as a ModuleScript.

It runs on your computer when you invoke it. No server, account, third-party packages, or Roblox credentials are needed.

## Try it

Requires Python 3.11 or newer. From the repository folder:

```sh
python flash_config.py examples/items.json --check
python flash_config.py examples/items.csv --output build/Items.luau
python -m unittest discover -s tests -v
```

On Windows, use `py` instead of `python` if that is how Python is installed.

Open the generated file and copy it into a ModuleScript named **Items** in ServerScriptService. If your project uses Rojo, put it in the directory mapped to that service instead. `examples/ReadCatalog.server.luau` shows how to build a lookup by item ID. A Studio plugin or importer is not required.

## Input

JSON is an array of objects. CSV uses these exact headers, in any order:

| Field | Required | Meaning |
| --- | --- | --- |
| id | Yes | Unique, case-sensitive identifier: letter first, then letters, digits, underscore or hyphen; maximum 64 ASCII characters. |
| name | Yes | Nonblank display text, up to 120 Unicode code points. |
| price | Yes | Whole currency units, from 0 to 9007199254740991. JSON booleans and decimal numbers are rejected. |
| requires | No | Another item ID that must already be owned. Empty CSV cells mean no prerequisite; omit the field in JSON. |

The catalog may contain 1–10,000 items and must fit in 1 MiB of UTF-8 text. UTF-8 BOMs are accepted. Unknown fields, duplicate JSON fields or CSV headers, missing references, self-references and prerequisite cycles fail validation. CSV prices use plain decimal digits, without leading zeros except for zero itself.

## Output and errors

- `--check` validates without creating a file.
- `--output path.luau` generates an array in source order. Each row and the outer table are frozen. References remain ID strings.
- A successful command prints an item count and exits 0. Invalid input or a file error prints an explanation to stderr and exits 1. Incorrect CLI usage exits 2.
- Output is deterministic and replaced atomically after validation. A validation failure leaves existing output intact. Parent directories are created when needed.

The generated module only holds data. It does not grant items, enforce prerequisites, save balances, or validate purchase requests. Those responsibilities belong in your game's server code. There is no upload or live synchronization.

## Checks and scope

Tests cover malformed inputs, reference cycles, Unicode escaping, a long prerequisite chain, CSV/JSON agreement, command exit codes and preserving output on failure. CI also loads a generated module in Lune and checks its values and frozen tables. A live Roblox Studio integration check remains separate.

[Tarmac](https://github.com/Roblox/tarmac) is an existing Roblox resource compiler and asset manager. Comparing its scope helped keep this project focused: Flash Config handles a small item-data format and generates source; it does not process or upload assets. [Rojo](https://github.com/rojo-rbx/rojo) can handle syncing that source into Studio. No code was copied from either project.

MIT licensed. See [LICENSE](LICENSE).
