def formatDropItem(li):
    msg = '获得掉落物：'
    for item in li:
        if item["have"]:
            msg += '{}({}) '.format(item['name'], item["quantity"])
    return msg[:-1]


def formatTimeDisplay(second):
    if not isinstance(second, (int, float)):
        try:
            second = float(second)
        except (TypeError, ValueError):
            return second
    day = int(second / (24 * 3600))
    tl = second % (24 * 3600)
    hour = int(tl / 3600)
    tl = tl % 3600
    minute = int(tl / 60)
    tl = tl % 60
    sec = tl / 1
    tl = tl % 1
    msecs = round(tl, 3)
    o = ''
    if day != 0:
        o = o + '%s天' % int(day)
    if hour != 0:
        o = o + '%s时' % int(hour)
    if minute != 0:
        o = o + '%s分' % int(minute)
    if sec != 0:
        o = o + '%s秒' % int(sec)
    if msecs != 0:
        o = o + str(msecs)[2:] + '毫秒'
    return o


def formatBytes(bytes_len: int):
    return f"{bytes_len}Bytes"
