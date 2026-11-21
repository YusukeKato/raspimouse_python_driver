"""Lazy import of lgpio (apt: python3-lgpio)."""

from ...exceptions import BackendUnavailableError


def import_lgpio():
    """Return the lgpio module, or raise BackendUnavailableError."""
    try:
        import lgpio
    except ImportError as e:
        raise BackendUnavailableError(
            'lgpio is not installed (sudo apt install python3-lgpio)') from e
    return lgpio
