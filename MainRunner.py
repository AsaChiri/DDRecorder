import datetime
import logging
import threading
import time
import traceback
from multiprocessing import Process, Value

import utils
from BiliLive import BiliLive
from BiliLiveRecorder import BiliLiveRecorder
from BiliVideoChecker import BiliVideoChecker
from DanmuRecorder import BiliDanmuRecorder
from Processor import Processor
from Uploader import Uploader


class MainRunner():
    def __init__(self, config):
        self.config = config
        self.prev_live_status = False
        self.current_state = Value(
            'i', int(utils.state.WAITING_FOR_LIVE_START))
        self.state_change_time = Value('f', time.time())
        if self.config.get('root', {}).get('enable_baiduyun', False):
            from bypy import ByPy
            _ = ByPy()
        self.bl = BiliLive(self.config)
        self.blr = None
        self.bdr = None

    def proc(self, config: dict, record_dir: str, danmu_path: str, current_state, state_change_time) -> None:
        p = Processor(config, record_dir, danmu_path)
        p.run()

        if config.get('spec', {}).get('uploader', {}).get('record', {}).get('upload_record', False) or config.get('spec', {}).get('uploader', {}).get('clips', {}).get('upload_clips', False):
            current_state.value = int(utils.state.UPLOADING_TO_BILIBILI)
            state_change_time.value = time.time()
            u = Uploader(p.outputs_dir, p.splits_dir, config)
            if u.uploader.access_token is None:
                current_state.value = int(utils.state.ERROR)
                state_change_time.value = time.time()
                return
            d = u.upload(p.global_start)
            if not config.get('spec', {}).get('uploader', {}).get('record', {}).get('keep_record_after_upload', True) and d.get("record", None) is not None and not config.get('root', {}).get('uploader', {}).get('upload_by_edit', False):
                rc = BiliVideoChecker(d['record']['bvid'],
                                      p.splits_dir, config)
                rc.start()
            if not config.get('spec', {}).get('uploader', {}).get('clips', {}).get('keep_clips_after_upload', True) and d.get("clips", None) is not None and not config.get('root', {}).get('uploader', {}).get('upload_by_edit', False):
                cc = BiliVideoChecker(d['clips']['bvid'],
                                      p.outputs_dir, config)
                cc.start()

        if config.get('root', {}).get('enable_baiduyun', False) and config.get('spec', {}).get('backup', False):
            current_state.value = int(utils.state.UPLOADING_TO_BAIDUYUN)
            state_change_time.value = time.time()
            try:
                from bypy import ByPy
                bp = ByPy()
                bp.upload(p.merged_file_path)
            except Exception as e:
                logging.error('Error when uploading to Baiduyun:' +
                              str(e)+traceback.format_exc())
                current_state.value = int(utils.state.ERROR)
                state_change_time.value = time.time()
                return

        if current_state.value != int(utils.state.LIVE_STARTED):
            current_state.value = int(utils.state.WAITING_FOR_LIVE_START)
            state_change_time.value = time.time()

    def run(self):
        try:
            while True:
                if not self.prev_live_status and self.bl.live_status:
                    start = datetime.datetime.now()
                    self.blr = BiliLiveRecorder(self.config, start)
                    self.bdr = BiliDanmuRecorder(self.config, start)
                    record_process = Process(
                        target=self.blr.run)
                    danmu_process = Process(
                        target=self.bdr.run)
                    danmu_process.start()
                    record_process.start()

                    self.current_state.value = int(utils.state.LIVE_STARTED)
                    self.state_change_time.value = time.time()
                    self.prev_live_status = True

                    record_process.join()
                    danmu_process.join()

                    self.current_state.value = int(
                        utils.state.PROCESSING_RECORDS)
                    self.state_change_time.value = time.time()

                    self.prev_live_status = False
                    proc_process = Process(target=self.proc, args=(
                        self.config, self.blr.record_dir, self.bdr.danmu_dir, self.current_state, self.state_change_time))
                    proc_process.start()
                    try:
                        self.bl.__live_status = self.bl.check_live_status()
                        self.bl.__last_check_time = datetime.datetime.now()
                    except Exception as e:
                        logging.error(
                            "Status Error"+str(e)+traceback.format_exc())
                else:
                    time.sleep(self.config.get(
                        'root', {}).get('check_interval', 60))
        except KeyboardInterrupt:
            return
        except Exception as e:
            logging.error('Error in Mainrunner:' +
                          str(e)+traceback.format_exc())
            self.current_state.value = int(utils.state.ERROR)
            self.state_change_time.value = time.time()
            return


class MainThreadRunner(threading.Thread):
    def __init__(self, config):
        threading.Thread.__init__(self)
        self.mr = MainRunner(config)

    def run(self):
        self.mr.run()
