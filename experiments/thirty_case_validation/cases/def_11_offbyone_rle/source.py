def rle(data):
    """Run-length encode a string into (char, count) pairs.

    Contract:
      * every character is emitted exactly once, with its run count.
      * 'aaabb' -> [('a',3),('b',2)].
    """
    out = []
    i = 0
    n = len(data)
    while i < n:
        j = i
        while j < n and data[j] == data[i]:
            j += 1
        out.append((data[i], j - i + 1))
        i = j
    return out
