def total(prices, discount=0.0):
    """Sum prices, applying a discount percentage in [0, 100].

    Contract:
      * no discount (the historical behaviour) returns the plain sum.
      * a discount of d percent returns sum * (1 - d/100).
      * an empty list returns 0.0.
    """
    base = sum(prices)
    return base * (1.0 - discount / 100.0)
