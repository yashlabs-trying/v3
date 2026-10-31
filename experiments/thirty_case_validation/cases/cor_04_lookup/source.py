def lookup(primary, fallback, key):
    """Return primary[key], else fallback[key], else None.

    Contract:
      * value from the primary source is preferred when the key is present.
      * the fallback is used only when the primary lacks the key.
      * a missing key in both returns None.
    """
    if key in primary:
        return primary[key]
    if key in fallback:
        return fallback[key]
    return None
