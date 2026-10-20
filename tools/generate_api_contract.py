"""Regenerate the two API specifications and marked documentation inventories."""

from __future__ import annotations

import inspect
import sys
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))


def main() -> None:
    app = import_module("app_base.main").app
    write_artifacts = import_module("contract_artifacts").write_artifacts
    sources = {}
    for route in app.routes:
        endpoint = getattr(route, "endpoint", None)
        if endpoint is None:
            continue
        source_file = inspect.getsourcefile(endpoint)
        if source_file is None or not Path(source_file).is_relative_to(ROOT):
            continue
        source = f"{Path(source_file).relative_to(ROOT).as_posix()}:{inspect.getsourcelines(endpoint)[1]}"
        for method in getattr(route, "methods", set()):
            sources[(method.lower(), route.path)] = source
    write_artifacts(app.openapi(), sources)


if __name__ == "__main__":
    main()
