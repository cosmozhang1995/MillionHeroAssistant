# -*- coding:utf-8 -*-


"""

    Xi Gua video Million Heroes

"""
import multiprocessing
import operator
import sys, os
import time
from argparse import ArgumentParser
from datetime import datetime
from functools import partial
from multiprocessing import Event, Pipe
from textwrap import wrap

from config import api_key, enable_chrome, use_monitor, image_compress_level, crop_areas
from config import api_version
from config import app_id
from config import app_key
from config import app_secret
from config import data_directory
from config import prefer
from config import use_monitor
from config import answer_time_limits
from config import detecting_interval
from core.android import save_screen, check_screenshot, get_adb_tool, analyze_current_screen_text
from core.check_words import parse_false
from core.chrome_search import run_browser
from core.crawler.baiduzhidao import baidu_count
from core.crawler.crawl import jieba_initialize, kwquery
from core.ocr.baiduocr import get_text_from_image as bai_get_text
from core.ocr.spaceocr import get_text_from_image as ocrspace_get_text
## jieba init
from dynamic_table import clear_screen

jieba_initialize()

if prefer[0] == "baidu":
    get_text_from_image = partial(bai_get_text,
                                  app_id=app_id,
                                  app_key=app_key,
                                  app_secret=app_secret,
                                  api_version=api_version,
                                  timeout=5)

elif prefer[0] == "ocrspace":
    get_test_from_image = partial(ocrspace_get_text, api_key=api_key)


def parse_args():
    parser = ArgumentParser(description="Million Hero Assistant")
    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=5,
        help="default http request timeout"
    )
    return parser.parse_args()


def parse_question_and_answer(text_list):
    question = ""
    start = 0
    for i, keyword in enumerate(text_list):
        question += keyword
        if "?" in keyword:
            start = i + 1
            break
    real_question = question.split(".")[-1]

    for char, repl in [("以下", ""), ("下列", "")]:
        real_question = real_question.replace(char, repl, 1)

    question, true_flag = parse_false(real_question)
    return true_flag, real_question, question, text_list[start:]


def pre_process_question(keyword):
    """
    strip charactor and strip ?
    :param question:
    :return:
    """
    now = datetime.today()
    for char, repl in [("“", ""), ("”", ""), ("？", ""), ("《", ""), ("》", ""), ("我国", "中国"),
                       ("今天", "{0}年{1}月{2}日".format(now.year, now.month, now.day)),
                       ("今年", "{0}年".format(now.year)),
                       ("这个月", "{0}年{1}月".format(now.year, now.month))]:
        keyword = keyword.replace(char, repl)

    keyword = keyword.split(r"．")[-1]
    keywords = keyword.split(" ")
    keyword = "".join([e.strip("\r\n") for e in keywords if e])
    return keyword


def main():
    args = parse_args()
    timeout = args.timeout

    adb_bin = get_adb_tool()
    if use_monitor:
        os.system("{0} connect 127.0.0.1:62001".format(adb_bin))

    check_screenshot(filename="screenshot.png", directory=data_directory)

    # stdout_queue = Queue(10)
    # ## spaw baidu count
    # baidu_queue = Queue(5)
    # baidu_search_job = multiprocessing.Process(target=baidu_count_daemon,
    #                                            args=(baidu_queue, stdout_queue, timeout))
    # baidu_search_job.daemon = True
    # baidu_search_job.start()
    #
    # ## spaw crawler
    # knowledge_queue = Queue(5)
    # knowledge_craw_job = multiprocessing.Process(target=crawler_daemon,
    #                                              args=(knowledge_queue, stdout_queue))
    # knowledge_craw_job.daemon = True
    # knowledge_craw_job.start()
    #
    # ## output threading
    # output_job = threading.Thread(target=print_terminal, args=(stdout_queue,))
    # output_job.daemon = True
    # output_job.start()

    if enable_chrome:
        closer = Event()
        noticer = Event()
        noticer.clear()
        reader, writer = Pipe()
        browser_daemon = multiprocessing.Process(
            target=run_browser, args=(closer, noticer, reader,))
        browser_daemon.daemon = True
        browser_daemon.start()

    last_question = None

    def __inner_job():
        start = time.time()
        text_binary = analyze_current_screen_text(
            directory=data_directory,
            compress_level=image_compress_level[0],
            crop_area=crop_areas[game_type],
            use_monitor=use_monitor
        )
        keywords = get_text_from_image(
            image_data=text_binary,
            timeout=timeout
        )
        if not keywords:
            # print("\ntext not recognize")
            return None

        true_flag, real_question, question, answers = parse_question_and_answer(keywords)

        nonlocal last_question

        if last_question == real_question:
            return None

        last_question = real_question

        ## notice crawler to work
        # qwriter.send(real_question.strip("?"))
        # crawler_noticer.set()
        
        print("")

        print('-' * 72)
        print("\033[43;34m\033[1m" + real_question + "\033[0m")
        # print('-' * 72)
        # print("\n".join(answers))

        if game_type == "UC答题":
            answers = map(lambda a: a.rsplit(":")[-1], answers)

        print("~" * 60)
        print("{0}\n{1}".format(real_question, "\n".join(answers)))
        print("~" * 60)

        # ### refresh question
        # stdout_queue.put({
        #     "type": 0,
        #     "data": "{0}\n{1}".format(question, "\n".join(answers))
        # })
        #
        # # notice baidu and craw
        # baidu_queue.put((
        #     question, answers, true_flag
        # ))
        # knowledge_queue.put(question)

        if enable_chrome:
            writer.send(question)
            noticer.set()

        summary = baidu_count(question, answers, timeout=timeout)
        summary_li = sorted(summary.items(), key=operator.itemgetter(1), reverse=True)
        if true_flag:
            print("肯定回答(**)： ", "\033[43;31m\033[1m" + summary_li[0][0] + "\033[0m")
            print("否定回答(  )： ", summary_li[-1][0])
        else:
            print("肯定回答(  )： ", summary_li[0][0])
            print("否定回答(**)： ", "\033[43;31m\033[1m" + summary_li[-1][0] + "\033[0m")
        print("*" * 72)

        end = time.time()
        # stdout_queue.put({
        #     "type": 3,
        #     "data": "use {0} 秒".format(end - start)
        # })
        print("use {0} 秒".format(end - start))
        save_screen(
            directory=data_directory
        )
        time.sleep(1)

        return real_question

    print("""
            请选择答题节目:
              1. 百万英雄
              2. 冲顶大会
              3. 芝士超人
              4. UC答题
            """)
    game_type = input("输入节目序号: ")
    if game_type == "1":
        game_type = '百万英雄'
    elif game_type == "2":
        game_type = '冲顶大会'
    elif game_type == "3":
        game_type = "芝士超人"
    elif game_type == "4":
        game_type = "UC答题"
    else:
        game_type = '百万英雄'
    
    print("""
    请在答题开始前就运行程序，
    答题开始的时候按Enter预测答案
                """)
    print("当前选择答题游戏: {}\n".format(game_type))

    ret_val = None

    while True:
        enter = input("按Enter键开始，按ESC键退出...")
        if enter == chr(27):
            break
        try:
            clear_screen()
            ret_val = __inner_job()
        # if ret_val is None:
        #     sys.stdout.write(("\r%- 15s" % datetime.now().strftime("%H:%M:%S.%f")) + " 未检测到题目 / 题目无变化")
        #     time.sleep(detecting_interval)
        # else:
        #     timelimit = float(answer_time_limits[game_type])
        #     timewait = 0.0
        #     while timewait < timelimit:
        #         timewait += detecting_interval
        #         time.sleep(detecting_interval)
        #         sys.stdout.write("\r检测到题目，下一次检测将在% 2.2fs后开始" % (timelimit - timewait))
        #     print("")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(str(e))

    print("欢迎下次使用")
    if enable_chrome:
        reader.close()
        writer.close()
        closer.set()
        time.sleep(3)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
