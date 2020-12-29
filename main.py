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


def proc(config: dict, record_dir: str, danmu_path: str) -> None:
    p = Processor(config, record_dir, danmu_path)
    p.run()
    u = Uploader(p.outputs_dir, p.splits_dir, config)
    u.upload(p.global_start)


if __name__ == "__main__":
    root_config_filename = sys.argv[1]
    spec_config_filename = sys.argv[2]
    with open(root_config_filename, "r") as f:
        root_config = json.load(f)
    with open(spec_config_filename, "r") as f:
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
                        filename=os.path.join(config['root']['logger']['log_path'], datetime.datetime.now(
                        ).strftime('%Y-%m-%d_%H-%M-%S')+'.log'),
                        filemode='a')
    utils.init_data_dirs(config['root']['global_path']['data_path'])
    bl = BiliLive(config)
    prev_live_status = False
    while True:
        if not prev_live_status and bl.live_status:
            print("开播啦~")
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
