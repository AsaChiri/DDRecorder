import datetime
import logging
import os
import traceback
import json
from biliup.plugins.bili_webup import BiliBili, Data

import utils
from BiliLive import BiliLive


class Uploader(BiliLive):
    def __init__(self, output_dir: str, splits_dir: str, config: dict):
        super().__init__(config)
        self.output_dir = output_dir
        self.splits_dir = splits_dir

        self.uploader = BiliBili(Data())
        self.lines = config.get("root", {}).get(
            "uploader", {}).get("lines", "AUTO")
        account = {'account':
                   {
                       'username': self.config.get('spec', {}).get('uploader', {}).get('account', {}).get('username', ""),
                       'password': self.config.get('spec', {}).get('uploader', {}).get('account', {}).get('password', "")
                   },
                   'access_token': self.config.get('spec', {}).get('uploader', {}).get('account', {}).get('access_token', ''),
                   'refresh_token': self.config.get('spec', {}).get('uploader', {}).get('account', {}).get('refresh_token', ''),
                   'cookies': self.config.get('spec', {}).get('uploader', {}).get('account', {}).get('cookies', None)}

        try:
            self.uploader.login(utils.get_cred_filename(
                self.room_id, self.config.get('root', {}).get('data_path', "./")), account)
        except Exception as e:
            logging.error(self.generate_log(
                'Error while login:' + str(e)+traceback.format_exc()))
            raise(e)

    def upload(self, global_start: datetime.datetime) -> dict:
        logging.basicConfig(level=utils.get_log_level(self.config),
                            format='%(asctime)s %(thread)d %(threadName)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S',
                            filename=os.path.join(self.config.get('root', {}).get('logger', {}).get('log_path', "./log"), "Uploader_"+datetime.datetime.now(
                            ).strftime('%Y-%m-%d_%H-%M-%S')+'.log'),
                            filemode='a')
        return_dict = {}
        datestr = global_start.strftime(
            '%Y{y}%m{m}%d{d}').format(y='年', m='月', d='日')
        format_dict = {"date": datestr,
                       "year": global_start.year,
                       "month": global_start.month,
                       "day": global_start.day,
                       "hour": global_start.hour,
                       "minute": global_start.minute,
                       "second": global_start.second,
                       "rough_time": utils.get_rough_time(global_start.hour),
                       "room_name": self.room_info['room_name']}
        try:
            if self.config.get('spec', {}).get('uploader', {}).get('clips', {}).get('upload_clips', False):
                clips_video_data = Data()
                clips_video_data.copyright = self.config.get('spec', {}).get(
                    'uploader', {}).get('copyright', 2)
                clips_video_data.title = self.config.get('spec', {}).get(
                    'uploader', {}).get('clips', {}).get('title', "").format(**format_dict)
                clips_video_data.desc = self.config.get('spec', {}).get(
                    'uploader', {}).get('clips', {}).get('desc', "").format(**format_dict)
                clips_video_data.source = "https://live.bilibili.com/"+self.room_id
                clips_video_data.tid = self.config.get('spec', {}).get(
                    'uploader', {}).get('clips', {}).get('tid', 27)
                clips_video_data.set_tag(self.config.get('spec', {}).get(
                    'uploader', {}).get('clips', {}).get('tags', []))

                self.uploader.video = clips_video_data
                filelists = os.listdir(self.output_dir)
                filelists.sort(key=lambda x: int(
                    "".join(os.path.splitext(x)[0].split("_")[-2].split("-"))))
                for filename in filelists:
                    if os.path.getsize(os.path.join(self.output_dir, filename)) < 1024*1024:
                        continue
                    file_path = os.path.join(self.output_dir, filename)
                    video_part = self.uploader.upload_file(
                        file_path, lines=self.lines)
                    video_part['title'] = os.path.splitext(filename)[
                        0].split("_")[-1]
                    video_part['desc'] = self.config.get('spec', {}).get('uploader', {}).get(
                        'clips', {}).get('desc', "").format(**format_dict)
                    clips_video_data.append(video_part)
                if len(clips_video_data.videos) == 0:
                    logging.warn(self.generate_log(
                    '没有可用于上传的自动切片！'))
                    self.uploader.video = None
                else:
                    if os.path.exists(self.config.get('spec', {}).get(
                            'uploader', {}).get('clips', {}).get('cover', "")):
                        clips_video_data.cover = self.uploader.cover_up(self.config.get('spec', {}).get(
                            'uploader', {}).get('clips', {}).get('cover', ""))
                    
                    clips_video_ret = self.uploader.submit()
                    if clips_video_ret['code'] == 0 and clips_video_ret['data'] is not None:
                        return_dict["clips"] = {
                            "avid": clips_video_ret['data']['aid'],
                            "bvid": clips_video_ret['data']['bvid']
                        }

            if self.config.get('spec', {}).get('uploader', {}).get('record', {}).get('upload_record', False):
                record_video_data = Data()
                record_video_data.copyright = self.config.get('spec', {}).get(
                    'uploader', {}).get('copyright', 2)
                record_video_data.title = self.config.get('spec', {}).get(
                    'uploader', {}).get('record', {}).get('title', "").format(**format_dict)
                record_video_data.desc = self.config.get('spec', {}).get(
                    'uploader', {}).get('record', {}).get('desc', "").format(**format_dict)
                record_video_data.source = "https://live.bilibili.com/"+self.room_id
                record_video_data.tid = self.config.get('spec', {}).get(
                    'uploader', {}).get('record', {}).get('tid', 27)
                record_video_data.set_tag(self.config.get('spec', {}).get(
                    'uploader', {}).get('record', {}).get('tags', []))

                self.uploader.video = record_video_data

                filelists = os.listdir(self.splits_dir)
                filelists.sort(key=lambda x: int(
                    os.path.splitext(x)[0].split("_")[-1]))
                for filename in filelists:
                    if os.path.getsize(os.path.join(self.splits_dir, filename)) < 1024*1024:
                        continue
                    file_path = os.path.join(self.splits_dir, filename)
                    video_part = self.uploader.upload_file(
                        file_path, lines=self.lines)
                    video_part['title'] = os.path.splitext(filename)[
                        0].split("_")[-1]
                    video_part['desc'] = self.config.get('spec', {}).get('uploader', {}).get(
                        'record', {}).get('desc', "").format(**format_dict)
                    record_video_data.append(video_part)
                if len(record_video_data.videos) == 0:
                    logging.warn(self.generate_log(
                    '没有可用于上传的录播分段！'))
                    self.uploader.video = None
                else:
                    if os.path.exists(self.config.get('spec', {}).get(
                            'uploader', {}).get('record', {}).get('cover', "")):
                        record_video_data.cover = self.uploader.cover_up(self.config.get('spec', {}).get(
                            'uploader', {}).get('record', {}).get('cover', ""))
                    record_video_ret = self.uploader.submit()
                    if record_video_ret['code'] == 0 and record_video_ret['data'] is not None:
                        return_dict["record"] = {
                            "avid": record_video_ret['data']['aid'],
                            "bvid": record_video_ret['data']['bvid']
                        }

        except Exception as e:
            logging.error(self.generate_log(
                'Error while uploading:' + str(e)+traceback.format_exc()))
            return None
        finally:
            self.uploader.close()

        return return_dict


if __name__ == '__main__':
    all_config_filename = 'config/config.spec.json'
    with open(all_config_filename, "r", encoding="UTF-8") as f:
        all_config = json.load(f)

    config = {
        'root': all_config.get('root', {}),
        'spec': all_config['spec'][0]
    }
    uploader = Uploader(
        output_dir='data\\data\\outputs\\8792912_2022-04-16_06-58-40', splits_dir='', config=config)
    uploader.upload(global_start=datetime.datetime.strptime(
        '2022-04-16_06-58-40', '%Y-%m-%d_%H-%M-%S'))
