import abc
import datetime
import logging
import traceback
import requests
import urllib3
from requests.adapters import HTTPAdapter

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class BaseLive(metaclass=abc.ABCMeta):

    def __init__(self, config: dict):

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
        self.session.mount('https://', HTTPAdapter(max_retries=3))
        self.room_id = ''
        self.site_name = ''
        self.site_domain = ''
        self.config = config
        self.__last_check_time = datetime.datetime.now(
        )+datetime.timedelta(seconds=-config.get('root', {}).get('check_interval', 60))
        self.__live_status = False
        self.__allowed_check_interval = datetime.timedelta(
            seconds=config.get('root', {}).get('check_interval', 60))

    def common_request(self, method: str, url: str, params: dict = None, data: dict = None) -> requests.Response:
        try:
            connection = None
            if method == 'GET':
                connection = self.session.get(
                    url, headers=self.headers, params=params, verify=False, timeout=5)
            if method == 'POST':
                connection = self.session.post(
                    url, headers=self.headers, params=params, data=data, verify=False, timeout=5)
            return connection
        except requests.exceptions.RequestException as e:
            logging.error(self.generate_log(
                "Request Error"+str(e)+traceback.format_exc()))

    @abc.abstractmethod
    def get_room_info(self):
        pass

    @abc.abstractmethod
    def get_live_urls(self):
        pass

    def __check_live_status(self) -> bool:
        self.room_info = self.get_room_info()
        if self.room_info['status']:
            logging.info(self.generate_log(
                "直播间标题："+self.room_info['room_name']))
            return True
        else:
            logging.info(self.generate_log("等待开播"))
        return False

    def check_live_status(self) -> bool:
        try:
            self.__live_status = self.__check_live_status()
            self.__last_check_time = datetime.datetime.now()
        except Exception as e:
            logging.error(self.generate_log(
                "Status Error" + str(e) + traceback.format_exc()))
        return self.__live_status

    @property
    def live_status(self) -> bool:
        if datetime.datetime.now()-self.__last_check_time >= self.__allowed_check_interval:
            logging.debug(self.generate_log("允许检查"))
            self.check_live_status()
        else:
            logging.debug(self.generate_log("间隔不足，使用过去状态"))
        return self.__live_status

    def generate_log(self, content: str = '') -> str:
        return f"[Site:{self.site_name} Room:{self.room_id}] {content}"
