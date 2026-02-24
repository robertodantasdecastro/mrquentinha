from pathlib import Path
import sys


def _ensure_backend_src_on_path() -> None:
    root_dir = Path(__file__).resolve().parent
    backend_src = root_dir / "workspaces" / "backend" / "src"

    if not backend_src.exists():
        return

    backend_src_str = str(backend_src)
    if backend_src_str not in sys.path:
        sys.path.insert(0, backend_src_str)


_ensure_backend_src_on_path()
