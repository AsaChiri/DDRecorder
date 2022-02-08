import datetime
import os
import logging
import traceback

from bilibiliuploader.bilibiliuploader import BilibiliUploader
from bilibiliuploader.core import VideoPart

from BiliLive import BiliLive
import utils


def upload(uploader: BilibiliUploader, parts: list, cr: int, title: str, tid: int, tags: list, desc: str, source: str, cover: str, thread_pool_workers: int = 1, max_retry: int = 3, upload_by_edit: bool = False) -> tuple:
    bvid = None
    if upload_by_edit:
        while bvid is None:
            avid, bvid = uploader.upload(
                parts=[parts[0]],
                copyright=cr,
                title=title,
                tid=tid,
                tag=",".join(tags),
                desc=desc,
                source=source,
                cover=cover,
                thread_pool_workers=thread_pool_workers,
                max_retry=max_retry,
            )
        for i in range(1, len(parts)):
            uploader.edit(
                bvid=bvid,
                parts=[parts[i]],
                max_retry=max_retry,
                thread_pool_workers=thread_pool_workers
            )
    else:
        while bvid is None:
            avid, bvid = uploader.upload(
                parts=parts,
                copyright=cr,
                title=title,
                tid=tid,
                tag=",".join(tags),
                desc=desc,
                source=source,
                cover=cover,
                thread_pool_workers=thread_pool_workers,
                max_retry=max_retry,
            )
            print(avid, bvid)
    return avid, bvid


class Uploader(BiliLive):
    def __init__(self, output_dir: str, splits_dir: str, config: dict):
        super().__init__(config)
        self.output_dir = output_dir
        self.splits_dir = splits_dir
        self.uploader = BilibiliUploader()
        try:
            if config.get('spec', {}).get('uploader', {}).get('account', {}).get('access_token', "") != "":
                try:
                    self.uploader.login_by_access_token(config.get('spec', {}).get('uploader', {}).get('account', {}).get(
                        'access_token', ""), config.get('spec', {}).get('uploader', {}).get('account', {}).get('refresh_token', ""))
                except Exception as e:
                    logging.warn(self.generate_log(
                        'Error while login with access token:' + str(e)+traceback.format_exc()))
                    self.uploader.login(config.get('spec', {}).get('uploader', {}).get('account', {}).get('username', ""),
                                        config.get('spec', {}).get('uploader', {}).get('account', {}).get('password', ""))
                    if self.uploader.access_token is not None:
                        self.uploader.save_login_data(utils.get_cred_filename(
                            self.room_id, config.get('root', {}).get('data_path', "./")))
            elif os.path.exists(utils.get_cred_filename(self.room_id, config.get('root', {}).get('data_path', "./"))):
                try:
                    self.uploader.login_by_access_token_file(utils.get_cred_filename(
                        self.room_id, config.get('root', {}).get('data_path', "./")))
                except Exception as e:
                    logging.warn(self.generate_log(
                        'Error while login with access token file:' + str(e)+traceback.format_exc()))
                    self.uploader.login(config.get('spec', {}).get('uploader', {}).get('account', {}).get('username', ""),
                                        config.get('spec', {}).get('uploader', {}).get('account', {}).get('password', ""))
                    if self.uploader.access_token is not None:
                        self.uploader.save_login_data(utils.get_cred_filename(
                            self.room_id, config.get('root', {}).get('data_path', "./")))
            else:
                self.uploader.login(config.get('spec', {}).get('uploader', {}).get('account', {}).get('username', ""),
                                    config.get('spec', {}).get('uploader', {}).get('account', {}).get('password', ""))
                if self.uploader.access_token is not None:
                    self.uploader.save_login_data(utils.get_cred_filename(
                        self.room_id, config.get('root', {}).get('data_path', "./")))
        except Exception as e:
            logging.error(self.generate_log(
                'Error while login:' + str(e)+traceback.format_exc()))


    def upload(self, global_start: datetime.datetime) -> dict:
        logging.basicConfig(level=utils.get_log_level(self.config),
                            format='%(asctime)s %(thread)d %(threadName)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S',
                            filename=os.path.join(self.config.get('root', {}).get('logger', {}).get('log_path', "./log"), "Uploader_"+datetime.datetime.now(
                            ).strftime('%Y-%m-%d_%H-%M-%S')+'.log'),
                            filemode='a')
        return_dict = {}
        try:
            if self.config.get('spec', {}).get('uploader', {}).get('clips', {}).get('upload_clips', False):
                output_parts = []
                datestr = global_start.strftime(
                    '%Y{y}%m{m}%d{d}').format(y='年', m='月', d='日')
                filelists = os.listdir(self.output_dir)
                for filename in filelists:
                    if os.path.getsize(os.path.join(self.output_dir, filename)) < 1024*1024:
                        continue
                    title = os.path.splitext(filename)[0].split("_")[-1]
                    output_parts.append(VideoPart(
                        path=os.path.join(self.output_dir, filename),
                        title=title,
                        desc=self.config.get('spec', {}).get('uploader', {}).get('clips', {}).get('desc', "").format(
                            date=datestr, year=global_start.year, month=global_start.month, day=global_start.day, hour=global_start.hour, minute=global_start.minute, second=global_start.second, rough_time=utils.get_rough_time(global_start.hour), room_name=self.room_info['room_name']),
                    ))

                avid, bvid = upload(self.uploader, output_parts,
                                    cr=self.config.get('spec', {}).get(
                                        'uploader', {}).get('copyright', 2),
                                    title=self.config.get('spec', {}).get('uploader', {}).get('clips', {}).get('title', "").format(
                                        date=datestr, year=global_start.year, month=global_start.month, day=global_start.day, hour=global_start.hour, minute=global_start.minute, second=global_start.second, rough_time=utils.get_rough_time(global_start.hour), room_name=self.room_info['room_name']),
                                    tid=self.config.get('spec', {}).get(
                                        'uploader', {}).get('clips', {}).get('tid', 27),
                                    tags=self.config.get('spec', {}).get(
                                        'uploader', {}).get('clips', {}).get('tags', []),
                                    desc=self.config.get('spec', {}).get('uploader', {}).get('clips', {}).get('desc', "").format(
                                        date=datestr, year=global_start.year, month=global_start.month, day=global_start.day, hour=global_start.hour, minute=global_start.minute, second=global_start.second, rough_time=utils.get_rough_time(global_start.hour), room_name=self.room_info['room_name']),
                                    source="https://live.bilibili.com/"+self.room_id,
                                    cover=self.config.get('spec', {}).get(
                                        'uploader', {}).get('clips', {}).get('cover', ""),
                                    thread_pool_workers=self.config.get('root', {}).get(
                                        'uploader', {}).get('thread_pool_workers', 1),
                                    max_retry=self.config.get('root', {}).get(
                                        'uploader', {}).get('max_retry', 10),
                                    upload_by_edit=self.config.get('root', {}).get('uploader', {}).get('upload_by_edit', False))
                return_dict["clips"] = {
                    "avid": avid,
                    "bvid": bvid
                }
            if self.config.get('spec', {}).get('uploader', {}).get('record', {}).get('upload_record', False):
                splits_parts = []
                datestr = global_start.strftime(
                    '%Y{y}%m{m}%d{d}').format(y='年', m='月', d='日')
                filelists = os.listdir(self.splits_dir)
                for filename in filelists:
                    if os.path.getsize(os.path.join(self.splits_dir, filename)) < 1024*1024:
                        continue
                    title = filename
                    splits_parts.append(VideoPart(
                        path=os.path.join(self.splits_dir, filename),
                        title=title,
                        desc=self.config.get('spec', {}).get('uploader', {}).get('record', {}).get('desc', "").format(
                            date=datestr, year=global_start.year, month=global_start.month, day=global_start.day, hour=global_start.hour, minute=global_start.minute, second=global_start.second, rough_time=utils.get_rough_time(global_start.hour), room_name=self.room_info['room_name']),
                    ))

                avid, bvid = upload(self.uploader, splits_parts,
                                    cr=self.config.get('spec', {}).get(
                                        'uploader', {}).get('copyright', 2),
                                    title=self.config.get('spec', {}).get('uploader', {}).get('record', {}).get('title', "").format(
                                        date=datestr, year=global_start.year, month=global_start.month, day=global_start.day, hour=global_start.hour, minute=global_start.minute, second=global_start.second, rough_time=utils.get_rough_time(global_start.hour), room_name=self.room_info['room_name']),
                                    tid=self.config.get('spec', {}).get(
                                        'uploader', {}).get('record', {}).get('tid', 27),
                                    tags=self.config.get('spec', {}).get(
                                        'uploader', {}).get('record', {}).get('tags', []),
                                    desc=self.config.get('spec', {}).get('uploader', {}).get('record', {}).get('desc', "").format(
                                        date=datestr, year=global_start.year, month=global_start.month, day=global_start.day, hour=global_start.hour, minute=global_start.minute, second=global_start.second, rough_time=utils.get_rough_time(global_start.hour), room_name=self.room_info['room_name']),
                                    source="https://live.bilibili.com/"+self.room_id,
                                    cover=self.config.get('spec', {}).get(
                                        'uploader', {}).get('record', {}).get('cover', ""),
                                    thread_pool_workers=self.config.get('root', {}).get(
                                        'uploader', {}).get('thread_pool_workers', 1),
                                    max_retry=self.config.get('root', {}).get(
                                        'uploader', {}).get('max_retry', 10),
                                    upload_by_edit=self.config.get('root', {}).get('uploader', {}).get('upload_by_edit', False))
                return_dict["record"] = {
                    "avid": avid,
                    "bvid": bvid
                }
        except Exception as e:
            logging.error(self.generate_log(
                'Error while uploading:' + str(e)+traceback.format_exc()))
        return return_dict
