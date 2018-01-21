# -*- coding: utf-8 -*-

"""

    use adb to capture the phone screen
    then use hanwang text recognize the text
    then use baidu to search answer

"""

import os
import platform
import subprocess
import sys
from datetime import datetime
from shutil import copyfile

from PIL import Image

def print(*args):
    pass

def exec_cmd(cmd):
    system_version = platform.system().upper()
    if system_version.startswith("WINDOWS"):
        os.system(cmd + " > NUL")
    else:
        os.system(cmd + " > /dev/null")

# SCREENSHOT_WAY 是截图方法，
# 经过 check_screenshot 后，会自动递
# 不需手动修改
SCREENSHOT_WAY = 3


last_iswhite = False


def get_adb_tool():
    system_version = platform.system().upper()
    adb_bin = ""
    parent = "adb"
    if system_version.startswith("LINUX"):
        adb_bin = os.path.join(parent, "linux", "adb")
    if system_version.startswith("WINDOWS"):
        adb_bin = os.path.join(parent, "win", "adb.exe")
    if system_version.startswith("DARWIN"):
        adb_bin = os.path.join(parent, "mac", "adb")
    return adb_bin


def check_screenshot(filename, directory):
    """
    检查获取截图的方式
    """
    save_shot_filename = os.path.join(directory, filename)
    global SCREENSHOT_WAY
    if os.path.isfile(save_shot_filename):
        try:
            os.remove(save_shot_filename)
        except Exception:
            pass
    if SCREENSHOT_WAY < 0:
        print("暂不支持当前设备")
        sys.exit()
    capture_screen(filename, directory)
    try:
        Image.open(save_shot_filename).load()
        print("采用方式 {} 获取截图".format(SCREENSHOT_WAY))
    except Exception:
        SCREENSHOT_WAY -= 1
        check_screenshot(filename=filename, directory=directory)


def analyze_current_screen_text(crop_area, white_area, rotate, white_thre, directory=".", compress_level=1, use_monitor=False):
    """
    capture the android screen now

    :return:
    """
    print("capture time: ", datetime.now().strftime("%H:%M:%S"))
    screenshot_filename = "screenshot.png"
    save_text_area = os.path.join(directory, "text_area.png")
    capture_screen_v2(screenshot_filename, directory)
    iswhite = parse_answer_area(os.path.join(directory, screenshot_filename),
                      save_text_area, compress_level, rotate, crop_area, white_area, white_thre)
    global last_iswhite
    if iswhite and not last_iswhite:
        last_iswhite = iswhite
        return get_area_data(save_text_area)
    else:
        last_iswhite = iswhite
        return None

def analyze_current_screen_text_v2(question_area, answer_area, white_area, rotate, white_thre, directory=".", compress_level=1, use_monitor=False, dont_set_white=False):
    """
    capture the android screen now

    :return:
    """
    print("capture time: ", datetime.now().strftime("%H:%M:%S"))
    screenshot_filename = "screenshot.png"
    save_question_area = os.path.join(directory, "question_area.png")
    save_answer_area = os.path.join(directory, "answer_area.png")
    capture_screen_v2(screenshot_filename, directory)
    iswhite = parse_question_answer_area(
        os.path.join(directory, screenshot_filename),
        save_question_area,
        save_answer_area,
        compress_level,
        rotate,
        question_area,
        answer_area,
        white_area,
        white_thre)
    global last_iswhite
    if iswhite and not last_iswhite:
        if not dont_set_white: last_iswhite = iswhite
        return (get_area_data(save_question_area), get_area_data(save_answer_area))
    else:
        if not dont_set_white: last_iswhite = iswhite
        return None


def analyze_stored_screen_text(screenshot_filename="screenshot.png", directory=".", compress_level=1):
    """
    reload screen from stored picture to store
    :param directory:
    :param compress_level:
    :return:
    """
    save_text_area = os.path.join(directory, "text_area.png")
    parse_answer_area(os.path.join(directory, screenshot_filename), save_text_area, compress_level)
    return get_area_data(save_text_area)


def capture_screen_v2(filename="screenshot.png", directory="."):
    """
    can't use general fast way

    :param filename:
    :param directory:
    :return:
    """
    adb_bin = get_adb_tool()
    exec_cmd("{0} shell screencap -p /sdcard/{1}".format(adb_bin, filename))
    exec_cmd("{0} pull /sdcard/{1} {2}".format(adb_bin, filename, os.path.join(directory, filename)))


def capture_screen(filename="screenshot.png", directory="."):
    """
    获取屏幕截图，目前有 0 1 2 3 四种方法，未来添加新的平台监测方法时，
    可根据效率及适用性由高到低排序

    :param filename:
    :param directory:
    :return:
    """
    global SCREENSHOT_WAY
    adb_bin = get_adb_tool()
    if 1 <= SCREENSHOT_WAY <= 3:
        process = subprocess.Popen(
            "{0} shell screencap -p".format(adb_bin),
            shell=True, stdout=subprocess.PIPE)
        binary_screenshot = process.stdout.read()
        if SCREENSHOT_WAY == 2:
            binary_screenshot = binary_screenshot.replace(b"\r\n", b"\n")
        elif SCREENSHOT_WAY == 1:
            binary_screenshot = binary_screenshot.replace(b"\r\r\n", b"\n")
        with open(os.path.join(directory, filename), "wb") as writer:
            writer.write(binary_screenshot)
    elif SCREENSHOT_WAY == 0:
        exec_cmd("{0} shell screencap -p /sdcard/{1}".format(adb_bin, filename))
        exec_cmd("{0} pull /sdcard/{1} {2}".format(adb_bin, filename, os.path.join(directory, filename)))


def save_screen(filename="screenshot.png", directory="."):
    """
    Save screen for further test
    :param filename:
    :param directory:
    :return:
    """
    copyfile(os.path.join(directory, filename),
             os.path.join(directory, datetime.now().strftime("%m%d_%H%M%S").join(os.path.splitext(filename))))


def parse_answer_area(source_file, text_area_file, compress_level, rotate, crop_area, white_area, white_thre):
    """
    crop the answer area

    :return:
    """

    image = Image.open(source_file)
    if compress_level == 1:
        image = image.convert("L")
    elif compress_level == 2:
        image = image.convert("1")

    if rotate == "left":
        image = image.rotate(90, expand=True)
    elif rotate == "right":
        image = image.rotate(-90, expand=True)

    width, height = image.size[0], image.size[1]
    print("screen width: {0}, screen height: {1}".format(width, height))

    for x in range(white_area[0], white_area[2]+1):
        for y in range(white_area[1], white_area[3]+1):
            pxrgb = image.getpixel((x,y))
            if pxrgb[0] < white_thre[0] or pxrgb[1] < white_thre[1] or pxrgb[2] < white_thre[2]:
                return False


    # region = image.crop(
    #     (width * crop_area[0], height * crop_area[1], width * crop_area[2], height * crop_area[3]))
    region = image.crop((crop_area[0], crop_area[1], crop_area[2], crop_area[3]))
    region.save(text_area_file)

    return True

def parse_question_answer_area(source_file, save_question_area, save_answer_area, compress_level, rotate, question_area, answer_area, white_area, white_thre):
    """
    crop the answer area

    :return:
    """

    image = Image.open(source_file)
    if compress_level == 1:
        image = image.convert("L")
    elif compress_level == 2:
        image = image.convert("1")

    if rotate == "left":
        image = image.rotate(90, expand=True)
    elif rotate == "right":
        image = image.rotate(-90, expand=True)

    width, height = image.size[0], image.size[1]
    print("screen width: {0}, screen height: {1}".format(width, height))

    for x in range(white_area[0], white_area[2]+1):
        for y in range(white_area[1], white_area[3]+1):
            pxrgb = image.getpixel((x,y))
            if pxrgb[0] < white_thre[0] or pxrgb[1] < white_thre[1] or pxrgb[2] < white_thre[2]:
                return False


    # region = image.crop(
    #     (width * crop_area[0], height * crop_area[1], width * crop_area[2], height * crop_area[3]))
    region = image.crop((question_area[0], question_area[1], question_area[2], question_area[3]))
    region.save(save_question_area)
    region = image.crop((answer_area[0], answer_area[1], answer_area[2], answer_area[3]))
    region.save(save_answer_area)

    return True


def get_area_data(text_area_file):
    """

    :param text_area_file:
    :return:
    """
    with open(text_area_file, "rb") as fp:
        image_data = fp.read()
        return image_data
    return ""
