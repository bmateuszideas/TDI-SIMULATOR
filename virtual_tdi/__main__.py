import sys

from .cli import main as cli_main
from .dataset import main as dataset_main
from .validation import main as validation_main


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "dataset":
        raise SystemExit(dataset_main(sys.argv[2:]))
    if len(sys.argv) >= 2 and sys.argv[1] == "validate":
        raise SystemExit(validation_main(sys.argv[2:]))
    if len(sys.argv) >= 2 and sys.argv[1] == "gui":
        try:
            from .gui import main as gui_main
        except Exception as exc:  # pragma: no cover - depends on Tk availability
            print(f"GUI unavailable: {exc}", file=sys.stderr)
            raise SystemExit(2)
        raise SystemExit(gui_main())
    raise SystemExit(cli_main(sys.argv[1:]))
