def hex2Int(xStr):
    return int(xStr[2:], 16)


def sum_hexs(hexs):
    sum = 0
    for h in hexs:
       x = h if isinstance(h, int) else int( h[2:], 16)
       sum += x

    return hex(sum)

def substract_hexs(hexs):
    t = None
    for h in hexs:
       if t is None:
          t = int(h[2:], 16)
          continue
       t -= int(h[2:], 16)

    return hex(t)
