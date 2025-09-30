# quest-designer

Prototype quest/state graph designer built with PySide6.

## Coding Style
We enforce snake_case for all project-defined functions, methods, variables, and module-level identifiers.

### Conventions
- Classes keep PascalCase (e.g. `QD_Node`, `QD_GfxScene`) – consistent with Qt / typical Python class naming.
- Qt / PySide6 framework overrides (e.g. `mousePressEvent`, `drawBackground`, `boundingRect`) remain in their original CamelCase because the Qt API requires those exact names for virtual method overrides.
- All previously existing camelCase helper methods have been refactored to snake_case (e.g. `add_input_socket`, `set_embedded_widget`, `update_path`). No deprecated camelCase aliases are kept.
- Signals follow snake_case (e.g. `zoom_changed`).

### Socket & Edge API (examples)
- `socket_type()`, `set_highlight(flag)`
- `finalize_with(socket)`, `update_dynamic_end(pos)`, `update_path()`
- Node accessors: `input_sockets()`, `output_sockets()`

### Rationale
Using a single convention for project-authored call sites improves readability and makes grep/search and refactors simpler. Keeping Qt override names untouched preserves framework integration and avoids subtle bugs from misnamed event handlers.

## Dynamic Import Shims
Some operational node modules use dynamic imports (`import_module('qdnodesocket')`) to work around analysis / path resolution issues. If your runtime package layout is finalized, you can replace these with standard imports.

## Requirements / Dependencies
- Python 3.11+
- PySide6

Install (example):
```bash
pip install PySide6
```

## Running
```bash
python -m src.main
```

## License
(Choose a license and update this section.)
