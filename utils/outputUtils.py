import numpy as np
import pandas as pd


def writeArray2Excel(nparray: np.ndarray, excelpath, sheet="page_1", float_format="%.5f"):
    writer = pd.ExcelWriter(excelpath)  # 写入Excel文件
    pd.DataFrame(nparray).to_excel(writer, sheet, float_format=float_format)
    writer.save()
    writer.close()
    return True


def writeArray2Image(nparray, imgpath, high_rgb, low_rgb):
    minv = np.min(nparray)
    maxv = np.max(nparray)
    # TODO:快去做
