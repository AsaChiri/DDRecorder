# -*- coding:utf-8 -*-

import datetime
import json
import logging
import os
import sys
import time
from multiprocessing import Process

import utils
from BiliLive import BiliLive
from BiliLiveRecorder import BiliLiveRecorder
from DanmuRecorder import BiliDanmuRecorder
from Processor import Processor
from Uploader import Uploader
from BiliVideoChecker import BiliVideoChecker


def proc(config: dict, record_dir: str, danmu_path: str) -> None:
    p = Processor(config, record_dir, danmu_path)
    p.run()
    u = Uploader(p.outputs_dir, p.splits_dir, config)
    d = u.upload(p.global_start)
    if not config['spec']['uploader']['record']['keep_record_after_upload'] and d.get("record", None) is not None:
        rc = BiliVideoChecker(d['record']['bvid'], p.splits_dir, config)
        rc_process = Process(
            target=rc.check)
        rc_process.start()
    if not config['spec']['uploader']['clips']['keep_clips_after_upload'] and d.get("clips", None) is not None:
        cc = BiliVideoChecker(d['clips']['bvid'], p.outputs_dir, config)
        cc_process = Process(
            target=cc.check)
        cc_process.start()
    if config['root']['enable_baiduyun'] and config['spec']['backup']:
        from bypy import ByPy
        bp = ByPy()
        bp.upload(p.merged_file_path)

if __name__ == "__main__":
    root_config_filename = sys.argv[1]
    spec_config_filename = sys.argv[2]
    with open(root_config_filename, "r", encoding="UTF-8") as f:
        root_config = json.load(f)
    with open(spec_config_filename, "r", encoding="UTF-8") as f:
        spec_config = json.load(f)
    config = {
        'root': root_config,
        'spec': spec_config
    }
    utils.check_and_create_dir(config['root']['global_path']['data_path'])
    utils.check_and_create_dir(config['root']['logger']['log_path'])
    logging.basicConfig(level=utils.get_log_level(config),
                        format='%(asctime)s %(thread)d %(threadName)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S',
                        handlers=[logging.FileHandler(os.path.join(config['root']['logger']['log_path'], "Main_"+datetime.datetime.now(
                        ).strftime('%Y-%m-%d_%H-%M-%S')+'.log'), "a", encoding="utf-8")])
    utils.init_data_dirs(config['root']['global_path']['data_path'])
    if config['root']['enable_baiduyun']:
        from bypy import ByPy
        bp = ByPy()
    #proc(config,"./data/data/records/22608112_2021-01-16_09-39-10","./data/data/danmu/22608112_2021-01-16_09-39-10_danmu.log")
    bl = BiliLive(config)
    prev_live_status = False
    while True:
        if not prev_live_status and bl.live_status:
            print(f"开播啦~现在是{datetime.datetime.now()}")
            prev_live_status = bl.live_status
            start = datetime.datetime.now()
            blr = BiliLiveRecorder(config, start)
            bdr = BiliDanmuRecorder(config, start)
            record_process = Process(
                target=blr.run)
            danmu_process = Process(
                target=bdr.run)
            danmu_process.start()
            record_process.start()
            record_process.join()
            danmu_process.join()
            prev_live_status = bl.live_status
            proc_process = Process(target=proc, args=(
                config, blr.record_dir, bdr.log_filename))
            proc_process.start()
        else:
            print("摸鱼中~")
            time.sleep(config['root']['check_interval'])
