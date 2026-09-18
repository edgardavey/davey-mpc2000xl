# Contributing

Architecture and current limitations are documented in
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/STATUS.md](docs/STATUS.md).

Bug reports should identify the host platform, source revision, MAME commit,
firmware version/hash, reproduction steps and observed behavior. Firmware,
disk contents, third-party samples and memory dumps must not be attached.

Source-only checks:

```bash
python3 tools/audit_public.py
python3 -m unittest discover -s tests
```

`PUBLIC_FILES.txt` lists the files included in a source release. The publication
audit validates that list and checks for private data and unapproved payloads.

Contributions to project-authored files use BSD-3-Clause. Adapted upstream code
retains its original license and attribution; dependencies are documented in
[THIRD_PARTY.md](THIRD_PARTY.md).
