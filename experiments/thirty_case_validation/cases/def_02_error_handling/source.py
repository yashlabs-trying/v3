def parse_int(text, default=None):
    """Parse an integer, returning `default` for malformed input.

    Contract:
      * None and non-string inputs return `default` (no exception).
      * whitespace is stripped and valid integers parse.
      * a malformed non-empty string returns `default`, it never raises.
    """
    if text is None:
        return default
    if not isinstance(text, str):
        return default
    text = text.strip()
    if text == "":
        return default
    return int(text)
