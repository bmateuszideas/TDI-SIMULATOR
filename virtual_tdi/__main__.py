import sys

from .core import cli_main, dataset_main
from .gui import main as gui_main, streamlit_main


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "dataset":
        raise SystemExit(dataset_main(sys.argv[2:]))
    if len(sys.argv) >= 2 and sys.argv[1] == "gui":
        raise SystemExit(gui_main())
    if len(sys.argv) >= 2 and sys.argv[1] == "dashboard":
        raise SystemExit(streamlit_main(sys.argv[2:]))
    raise SystemExit(cli_main(sys.argv[1:]))
