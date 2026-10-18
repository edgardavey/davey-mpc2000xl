# DAVEY patcher

`MPC2000XL-DAVEY-Patcher.html` : double-click, works offline in Safari, Chrome or Edge on Mac and Windows. Give it your original Akai OS 1.20
(`MPC2KXL.BIN`, sha256 100e3375...). Tick features, watch the point meter, create the file, confirm the three recovery checks, save.

`python3 engine.py original.BIN new.BIN [module ids]` does the same from a terminal; `--list` shows modules and points.

Read `STABILITY_GUIDE.md` first. Everything is emulator-tested only. Keep the original OS and check REC + OVER DUB recovery before flashing.
Rebuild after changing modules: `python3 gen_data.py && python3 build_app.py`. Gates: `python3 test_matrix.py`, `python3 test_features.py`.
