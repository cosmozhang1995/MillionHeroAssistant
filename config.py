# -*- coding:utf-8 -*-


import yaml

with open("config.yaml", "rb") as reader:
    config = yaml.safe_load(reader.read())

    data_directory = config["data_directory"]

    ### 1代表灰度处理， 2代表二值化处理，如果需要使用二值化，需要将2放到前面, 0不使用
    image_compress_level = config["image_compress_level"]

    ### 0 表示普通识别，配合compress_level 1使用
    ### 1 标识精确识别，精确识别建议配合image_compress_level 2使用
    api_version = config["api_version"]

    ## 图像比例裁剪区域, (left, top, right, bottom)
    crop_areas = config["crop_areas"]
    ## 问题区域
    question_areas = config["question_areas"]
    ## 答案选项区域
    answer_areas = config["answer_areas"]
    ## 图像上的白点位置（X,Y），该点判断为白色时，即认为弹出了题目框
    white_points = config["white_points"]
    ## 判断白点的阈值
    white_threshold = config["white_threshold"]
    ## 判断白点的邻域大小
    white_size = config["white_size"]

    # 截图预处理旋转方式，可选：no | left | right
    rotate = config["rotate"]

    # 从题目框出现到题目完全出现的时间
    question_waits = config["question_waits"]

    answer_time_limits = config["answer_time_limits"]
    detecting_interval = config["detecting_interval"]

    ### baidu orc
    app_id = config["app_id"]
    app_key = config["app_key"]
    app_secret = config["app_secret"]

    ### ocr.space
    api_key = config["api_key"]

    ### 默认使用百度，每天封顶500次
    ### 如果你想要使用ocr.space的话，将ocrspace移动到前面,每个api_key每月支持25000次调用
    prefer = config["prefer"]

    ### enable chrome
    enable_chrome = config["enable_chrome"]

    ### 是否使用夜神模拟器
    use_monitor = config["use_monitor"]
