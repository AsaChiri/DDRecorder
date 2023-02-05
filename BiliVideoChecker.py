import datetime
import logging
import os
import time
import threading
import requests
import urllib3
import utils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class BiliVideoChecker(threading.Thread):
    def __init__(self, bvid: str, path: str, config: dict):
        threading.Thread.__init__(self)
        default_headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4,zh-TW;q=0.2',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
        }
        self.headers = {**default_headers, **
                        config.get('root', {}).get('request_header', {})}
        self.session = requests.session()
        self.bvid = bvid
        self.path = path
        self.config = config
        self.check_url = "https://api.bilibili.com/x/web-interface/view"
        self.check_interval = config['root']['check_interval']

    def common_request(self, method: str, url: str, params: dict = None, data: dict = None) -> requests.Response:
        connection = None
        if method == 'GET':
            connection = self.session.get(
                url, headers=self.headers, params=params, verify=False)
        if method == 'POST':
            connection = self.session.post(
                url, headers=self.headers, params=params, data=data, verify=False)
        return connection

    def run(self) -> None:
        logging.basicConfig(level=utils.get_log_level(self.config),
                            format='%(asctime)s %(thread)d %(threadName)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S',
                            handlers=[logging.FileHandler(os.path.join(self.config.get('root', {}).get('logger', {}).get('log_path', "./log"), "VideoChecker_"+datetime.datetime.now(
                            ).strftime('%Y-%m-%d_%H-%M-%S')+'.log'), "a", encoding="utf-8")])
        while True:
            video_info = self.common_request("GET", self.check_url, {
                'bvid': self.bvid
            }).json()
            try:
                if video_info['code'] == 0 and video_info['data']['state'] == 0:
                    logging.info("稿件%s 已开放浏览，准备删除 %s", self.bvid, self.path)
                    utils.del_files_and_dir(self.path)
                    return
                else:
                    logging.info("稿件%s 未开放浏览", self.bvid)
                    time.sleep(self.check_interval)
            except KeyError:
                pass
