import datetime
import json
import logging
import os
import sys
import time
import threading
from multiprocessing import freeze_support
from lastversion import lastversion

import utils
from MainRunner import MainThreadRunner


CURRENT_VERSION = "1.2.2"



class versionThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        try:
            latest_version = lastversion.has_update(
                repo="AsaChiri/DDRecorder", current_version=CURRENT_VERSION)
            if latest_version:
                print('DDRecorder有更新，版本号: {} 请尽快到https://github.com/AsaChiri/DDRecorder/releases 下载最新版'.format(str(latest_version)))
            else:
                print('DDRecorder已是最新版本！')
        except:
            print('无法获取DDRecorder的版本信息，当前版本号: {}，请到https://github.com/AsaChiri/DDRecorder/releases 检查最新版本'.format(CURRENT_VERSION))



if __name__ == "__main__":
    freeze_support()
    vt = versionThread()
    vt.start()

    if utils.is_windows():
        utils.add_path("./ffmpeg/bin")

    try:
        if len(sys.argv) > 1:
            all_config_filename = sys.argv[1]
            with open(all_config_filename, "r", encoding="UTF-8") as f:
                all_config = json.load(f)
        else:
            with open("config.json", "r", encoding="UTF-8") as f:
                all_config = json.load(f)
    except Exception as e:
        print("解析配置文件时出现错误，请检查配置文件！")
        print("错误详情："+str(e))
        os.system('pause')

    utils.check_and_create_dir(all_config.get(
        'root', {}).get('data_path', "./"))
    utils.check_and_create_dir(all_config.get('root', {}).get(
        'logger', {}).get('log_path', './log'))
    logfile_name = "Main_"+datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+'.log'
    logging.basicConfig(level=utils.get_log_level(all_config),
                        format='%(asctime)s %(thread)d %(threadName)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S',
                        handlers=[logging.FileHandler(os.path.join(all_config.get('root', {}).get('logger', {}).get('log_path', "./log"), logfile_name), "a", encoding="utf-8")])
    utils.init_data_dirs(all_config.get('root', {}).get('data_path', "./"))
    if all_config.get('root', {}).get('enable_baiduyun', False):
        from bypy import ByPy
        bp = ByPy()

    runner_dict = {}
    for spec_config in all_config.get('spec', []):
        config = {
            'root': all_config.get('root', {}),
            'spec': spec_config
        }
        tr = MainThreadRunner(config)
        tr.setDaemon(True)
        runner_dict[spec_config['room_id']] = tr

    for tr in runner_dict.values():
        tr.start()
        time.sleep(10)

    while True:
        old_config = all_config
        try:
            if len(sys.argv) > 1:
                all_config_filename = sys.argv[1]
                with open(all_config_filename, "r", encoding="UTF-8") as f:
                    all_config = json.load(f)
            else:
                with open("config.json", "r", encoding="UTF-8") as f:
                    all_config = json.load(f)
        except Exception as e:
            print("解析配置文件时出现错误，请检查配置文件！已使用最后一次正确的配置")
            print("错误详情："+str(e))
            all_config = old_config
        utils.check_and_create_dir(all_config.get(
            'root', {}).get('data_path', "./"))
        utils.check_and_create_dir(all_config.get('root', {}).get(
            'logger', {}).get('log_path', './log'))
        logging.basicConfig(level=utils.get_log_level(all_config),
                            format='%(asctime)s %(thread)d %(threadName)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S',
                            handlers=[logging.FileHandler(os.path.join(all_config.get('root', {}).get('logger', {}).get('log_path', "./log"), logfile_name), "a", encoding="utf-8")])
        utils.init_data_dirs(all_config.get('root', {}).get('data_path', "./"))
        if all_config.get('root', {}).get('enable_baiduyun', False):
            from bypy import ByPy
            bp = ByPy()
        for spec_config in all_config.get('spec', []):
            config = {
                'root': all_config.get('root', {}),
                'spec': spec_config
            }
            if spec_config['room_id'] in runner_dict:
                runner_dict[spec_config['room_id']].mr.config = config
            else:
                tr = MainThreadRunner(config)
                tr.setDaemon(True)
                runner_dict[spec_config['room_id']] = tr
                tr.start()

        utils.print_log(runner_dict)
        time.sleep(all_config.get('root', {}).get('print_interval', 60))
