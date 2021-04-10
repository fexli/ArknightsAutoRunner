from . import imgops
from PIL import Image


def getCurrentEpisode(ark):
    return int(ark.reconizerN2.recognize2(imgops.clear_background(
        Image.fromarray(ark.getScreenShot(1059, 670, 56, 33)), 200), subset='0123456789')[0])
