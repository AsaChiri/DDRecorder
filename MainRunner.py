import datetime
import json
import logging
import os
import sys
import time
from multiprocessing import Process

import utils
from BaseLive import BaseLive
from BiliLive import BiliLive
from BiliLiveRecorder import BiliLiveRecorder
from DanmuRecorder import BiliDanmuRecorder
from Processor import Processor
from Uploader import Uploader
from BiliVideoChecker import BiliVideoChecker


class MainRunner(BaseLive):
    def __init__(self, config):
        super().__init__(config)
        self.prev_live_status = False
        self.current_state = utils.state.WAITING_FOR_LIVE_START
        self.state_change_time = datetime.datetime.now()
        if self.config['root']['enable_baiduyun']:
            from bypy import ByPy
            self.bp = ByPy()

    def proc(self, record_dir: str, danmu_path: str) -> None:
        p = Processor(self.config, record_dir, danmu_path)
        p.run()

        self.current_state = utils.state.UPLOADING_TO_BILIBILI
        self.state_change_time = datetime.datetime.now()
        u = Uploader(p.outputs_dir, p.splits_dir, self.config)
        d = u.upload(p.global_start)
        if not self.config['spec']['uploader']['record']['keep_record_after_upload'] and d.get("record", None) is not None:
            rc = BiliVideoChecker(d['record']['bvid'],
                                  p.splits_dir, self.config)
            rc_process = Process(
                target=rc.check)
            rc_process.start()
        if not self.config['spec']['uploader']['clips']['keep_clips_after_upload'] and d.get("clips", None) is not None:
            cc = BiliVideoChecker(d['clips']['bvid'],
                                  p.outputs_dir, self.config)
            cc_process = Process(
                target=cc.check)
            cc_process.start()

        self.current_state = utils.state.UPLOADING_TO_BAIDUYUN
        self.state_change_time = datetime.datetime.now()
        if self.config['root']['enable_baiduyun'] and self.config['spec']['backup']:
            self.bp.upload(p.merged_file_path)

    def run(self):

        # proc(config,"./data/data/records/22608112_2021-01-16_09-39-10","./data/data/danmu/22608112_2021-01-16_09-39-10_danmu.log")
        bl = BiliLive(self.config)
        while True:
            if not self.prev_live_status and bl.live_status:

                self.current_state = utils.state.LIVE_STARTED
                self.state_change_time = datetime.datetime.now()

                self.prev_live_status = bl.live_status
                start = datetime.datetime.now()
                blr = BiliLiveRecorder(self.config, start)
                bdr = BiliDanmuRecorder(self.config, start)
                record_process = Process(
                    target=blr.run)
                danmu_process = Process(
                    target=bdr.run)
                danmu_process.start()
                record_process.start()

                record_process.join()
                danmu_process.join()

                self.current_state = utils.state.PROCESSING_RECORDS
                self.state_change_time = datetime.datetime.now()
                self.prev_live_status = bl.live_status
                proc_process = Process(target=self.proc, args=(
                    blr.record_dir, bdr.log_filename))
                proc_process.start()
            else:
                time.sleep(self.config['root']['check_interval'])
