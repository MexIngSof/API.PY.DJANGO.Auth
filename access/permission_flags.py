"""Strict parsing for direct application-scoped permission grant decisions."""

_TRUE_VALUES = frozenset(("true", "1", "yes", "on", "y", "t"))
_FALSE_VALUES = frozenset(("false", "0", "no", "off", "n", "f"))


def parse_request_boolean(value: object) -> bool:
    """Accept explicit booleans, not Python truthiness of untrusted payloads."""
    if isinstance(value, bool):
        return value
    if type(value) is int and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in _TRUE_VALUES:
            return True
        if normalized in _FALSE_VALUES:
            return False
    raise ValueError("Allow must be an explicit boolean.")


def parse_permission_allow(value: object) -> bool:
    """Use the common fail-closed parser for RBAC grant decisions."""
    return parse_request_boolean(value)
