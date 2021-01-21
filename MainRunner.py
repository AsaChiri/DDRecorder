import datetime
import time
from multiprocessing import Process
import _thread
import threading
import logging
import utils
from BiliLive import BiliLive
from BiliLiveRecorder import BiliLiveRecorder
from DanmuRecorder import BiliDanmuRecorder
from Processor import Processor
from Uploader import Uploader
from BiliVideoChecker import BiliVideoChecker
import traceback


class MainRunner(threading.Thread):
    def __init__(self, config):
        threading.Thread.__init__(self)
        self.config = config
        self.prev_live_status = False
        self.current_state = utils.state.WAITING_FOR_LIVE_START
        self.state_change_time = datetime.datetime.now()
        if self.config['root']['enable_baiduyun']:
            from bypy import ByPy
            bp = ByPy()
        self.bl = BiliLive(self.config)
        self.blr = None
        self.bdr = None

    def proc(self, record_dir: str, danmu_path: str) -> None:
        p = Processor(self.config, record_dir, danmu_path)
        p.run()
        
        if self.config['spec']['uploader']['record']['upload_record'] or self.config['spec']['uploader']['clips']['upload_clips']:
            self.current_state = utils.state.UPLOADING_TO_BILIBILI
            self.state_change_time = datetime.datetime.now()
            u = Uploader(p.outputs_dir, p.splits_dir, self.config)
            d = u.upload(p.global_start)
            if not self.config['spec']['uploader']['record']['keep_record_after_upload'] and d.get("record", None) is not None:
                rc = BiliVideoChecker(d['record']['bvid'],
                                    p.splits_dir, self.config)
                rc.start()
            if not self.config['spec']['uploader']['clips']['keep_clips_after_upload'] and d.get("clips", None) is not None:
                cc = BiliVideoChecker(d['clips']['bvid'],
                                    p.outputs_dir, self.config)
                cc.start()
        
        if self.config['root']['enable_baiduyun'] and self.config['spec']['backup']:
            self.current_state = utils.state.UPLOADING_TO_BAIDUYUN
            self.state_change_time = datetime.datetime.now()
            from bypy import ByPy
            bp = ByPy()
            bp.upload(p.merged_file_path)

        self.current_state = utils.state.WAITING_FOR_LIVE_START
        self.state_change_time = datetime.datetime.now()

    def run(self):
        try:
            while True:
                if not self.prev_live_status and self.bl.live_status:
                    self.current_state = utils.state.LIVE_STARTED
                    self.state_change_time = datetime.datetime.now()
                    self.prev_live_status = self.bl.live_status
                    start = datetime.datetime.now()
                    self.blr = BiliLiveRecorder(self.config, start)
                    self.bdr = BiliDanmuRecorder(self.config, start)
                    record_process = Process(
                        target=self.blr.run)
                    danmu_process = Process(
                        target=self.bdr.run)
                    danmu_process.start()
                    record_process.start()

                    record_process.join()
                    danmu_process.join()

                    self.current_state = utils.state.PROCESSING_RECORDS
                    self.state_change_time = datetime.datetime.now()
                    self.prev_live_status = self.bl.live_status
                    proc_thread = _thread.start_new_thread(self.proc, (
                        self.blr.record_dir, self.bdr.log_filename,))
                    proc_thread.start()
                else:
                    time.sleep(self.config['root']['check_interval'])
        except KeyboardInterrupt:
            return
        except Exception as e:
            logging.error('Error in Mainrunner:' +
                          str(e)+traceback.format_exc())
