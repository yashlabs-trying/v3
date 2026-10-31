def paginate(items, page, per_page):
    """Return the slice of items for a 1-based page number.

    Contract:
      * page is 1-based; page < 1 raises ValueError.
      * a page beyond the end returns an empty list (never an exception).
      * exactly `per_page` items are returned except on the final short page.
    """
    if page < 1:
        raise ValueError("page must be >= 1")
    if per_page < 1:
        raise ValueError("per_page must be >= 1")
    start = (page - 1) * per_page
    return items[start:start + per_page]
