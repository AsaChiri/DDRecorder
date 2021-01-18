import datetime
import json
import logging
import os
import sys
import time
from multiprocessing import Process

import utils
from MainRunner import MainRunner

if __name__ == "__main__":
    utils.add_path("./ffmpeg/bin")

    all_config_filename = sys.argv[1]
    with open(all_config_filename, "r", encoding="UTF-8") as f:
        all_config = json.load(f)

    utils.check_and_create_dir(all_config['root']['global_path']['data_path'])
    utils.check_and_create_dir(all_config['root']['logger']['log_path'])
    logging.basicConfig(level=utils.get_log_level(all_config),
                        format='%(asctime)s %(thread)d %(threadName)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S',
                        handlers=[logging.FileHandler(os.path.join(all_config['root']['logger']['log_path'], "Main_"+datetime.datetime.now(
                        ).strftime('%Y-%m-%d_%H-%M-%S')+'.log'), "a", encoding="utf-8")])
    utils.init_data_dirs(all_config['root']['global_path']['data_path'])
    if all_config['root']['enable_baiduyun']:
        from bypy import ByPy
        bp = ByPy()

    runner_list = []
    runner_process_list = []
    for spec_config in all_config['spec']:
        config = {
            'root': all_config['root'],
            'spec': spec_config
        }
        tr = MainRunner(config)
        runner_list.append(tr)
        trp = Process(target=tr.run)
        runner_process_list.append(trp)

    for trp in runner_process_list:
        trp.start()
    
    try:
        while True:
            utils.print_log(runner_list)
            time.sleep(all_config['root']['print_interval'])
    except KeyboardInterrupt :
        for trp in runner_process_list:
            trp.close()