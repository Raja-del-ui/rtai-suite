"""GUI package."""
# Lazy to avoid circular imports at import time
def _get_launcher():
    from .launcher import main as _main
    return _main

def launch_gui(*args, **kwargs):
    return _get_launcher()(*args, **kwargs)

__all__ = ["launch_gui"]
