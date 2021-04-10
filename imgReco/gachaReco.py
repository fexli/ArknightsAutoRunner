def getRecruitDetail(ark):
    p = []
    for i in range(4):
        x = 19 + 633 * (i % 2)
        y = 183 + 279 * (i // 2)
        w = 612
        h = 248
        img = ark.getScreenShot(x, y, w, h)
        if ark.gameTemp.dingwei("recruit\\rec_fin.png", img, 0.8):
            type_ = "FINISH"
        elif ark.gameTemp.dingwei("recruit\\remain.png", img, 0.8):
            type_ = "PROCESS"
        elif ark.gameTemp.dingwei("recruit\\rec_lock.png", img, 0.9):
            type_ = "LOCK"
        else:
            type_ = "READY"

        p.append({"id": i,
                  "type": type_,
                  "centre": [x + w / 2, y + h / 2],
                  "can": type_ == "READY"})
    return p
