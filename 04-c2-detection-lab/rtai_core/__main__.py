"""Package entry point - delegates to unified CLI."""
import sys
from rtai_core.cli_app import main
if __name__ == "__main__":
    raise SystemExit(main())
