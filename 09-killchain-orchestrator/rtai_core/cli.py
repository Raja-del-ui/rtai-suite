"""CLI boundary kit: exit codes, progress helpers, single error funnel."""

import enum
import sys

from rtai_core.exceptions import RTAIError


class ExitCode(enum.IntEnum):
    OK = 0
    USAGE = 2
    VALIDATION = 64
    STORAGE = 74
    TARGET = 75
    PROVIDER = 69
    AUTH = 77
    CONFIG = 78
    INTERNAL = 70


def banner(lines):
    print("*" * 62)
    for line in lines:
        print(f"  {line}")
    print("*" * 62)


def ok(message):
    print(f"[+] {message}")


def info(message):
    print(f"[*] {message}")


def warn(message):
    print(f"[!] warn: {message}", file=sys.stderr)


def fail(message, code=ExitCode.INTERNAL):
    print(f"[x] {message}", file=sys.stderr)
    return int(code)


def run_main(main_callable):
    """Wrap a CLI main() so RTAIError subclasses map to proper exit codes."""
    try:
        main_callable()
    except RTAIError as exc:
        return fail(str(exc), ExitCode(exc.exit_code))
    except KeyboardInterrupt:
        return fail("interrupted by operator", ExitCode.INTERNAL)
    return ExitCode.OK
