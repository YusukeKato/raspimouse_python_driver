"""Detection of the Raspberry Pi model this package runs on."""

from pathlib import Path

MODEL_PATH = Path('/proc/device-tree/model')


def read_model(path: Path = MODEL_PATH) -> str | None:
    """Return the board model string, or None if it cannot be read."""
    try:
        return path.read_bytes().rstrip(b'\x00').decode(errors='replace').strip()
    except OSError:
        return None


def is_raspberry_pi4(model: str | None = None) -> bool:
    """Return True if the board is a Raspberry Pi 4 (the only supported board)."""
    if model is None:
        model = read_model()
    return model is not None and model.startswith('Raspberry Pi 4')
