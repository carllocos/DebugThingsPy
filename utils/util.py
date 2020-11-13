def hex2Int(xStr):
    return int(xStr[2:], 16)


def sum_hexs(hexs):
    sum = 0
    for h in hexs:
       x = int( h[2:], 16)
       sum += x

    return hex(sum)

def substract_hexs(dev, adr):
    int_offs = int(dev.getOffset()[2:], 16)
    int_ad = int(adr[2:], 16)
    return hex(int_ad - int_offs)

