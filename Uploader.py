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

        account = get_account(self.config.get('spec', {}), config.get("root", {}))

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


def get_account(spec_config: dict, root_config: dict = None) -> dict:
    account_config = spec_config.get('uploader', {}).get('account', 'default')
    if isinstance(account_config, str) or not account_config:
        account_config = get_root_account_by_name(root_config, account_config)

    return {
            'account':
            {
                'username': account_config.get('username', ""),
                'password': account_config.get('password', "")
            },
            'access_token': account_config.get('access_token', ''),
            'refresh_token': account_config.get('refresh_token', ''),
            'cookies': account_config.get('cookies', None)
        }


def get_root_account_by_name(root_config: dict, name: str = None) -> dict:
    if not name:
        name = 'default'

    account = root_config.get('account', {}).get(name, {})
    if isinstance(account, str):
        with open(account, encoding='utf-8') as cookie_file:
            account = {"cookies": {}}
            cookie_json = json.load(cookie_file)
        for i in cookie_json["cookie_info"]["cookies"]:
            name = i["name"]
            account["cookies"][name] = i["value"]
        account["access_token"] = cookie_json["token_info"]["access_token"]
    return account


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='DDRecorder uploader')
    parser.add_argument('-c', '--config', type=str, default=None, required=True, help='配置文件路径')
    parser.add_argument('-i', '--spec_index', type=int, default=0, help='spec 索引，从0开始计数')
    parser.add_argument('-o', '--output_dir', type=str, default='', help='切片的保存目录')
    parser.add_argument('-s', '--splits_dir', type=str, default='', help='splits dir')

    args = parser.parse_args()

    with open(args.config, "r", encoding="UTF-8") as f:
        all_config = json.load(f)

    config = {
        'root': all_config.get('root', {}),
        'spec': all_config['spec'][args.spec_index]
    }
    uploader = Uploader(
        output_dir=args.output_dir, splits_dir=args.splits_dir, config=config)

    media_path = args.output_dir or args.splits_dir
    time_str = '_'.join(os.path.basename(media_path).split('_')[1:])
    start_time = datetime.datetime.strptime(time_str, '%Y-%m-%d_%H-%M-%S')
    uploader.upload(global_start=start_time)
