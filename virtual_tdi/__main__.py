import sys

from .cli import main as cli_main
from .dataset import main as dataset_main
from .gui import main as gui_main


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "dataset":
        raise SystemExit(dataset_main(sys.argv[2:]))
    if len(sys.argv) >= 2 and sys.argv[1] == "gui":
        raise SystemExit(gui_main())
    raise SystemExit(cli_main(sys.argv[1:]))
