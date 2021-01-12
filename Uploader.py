import datetime
import os
import logging

from bilibiliuploader.bilibiliuploader import BilibiliUploader
from bilibiliuploader.core import VideoPart

from BiliLive import BiliLive
import utils


class Uploader(BiliLive):
    def __init__(self, output_dir: str, splits_dir: str, config: dict):
        super().__init__(config)
        self.output_dir = output_dir
        self.splits_dir = splits_dir
        self.uploader = BilibiliUploader()
        self.uploader.login(config['spec']['uploader']['account']['username'],
                            config['spec']['uploader']['account']['password'])

    def upload(self, global_start: datetime.datetime) -> dict:
        logging.basicConfig(level=utils.get_log_level(self.config),
                            format='%(asctime)s %(thread)d %(threadName)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S',
                            filename=os.path.join(self.config['root']['logger']['log_path'], "Uploader_"+datetime.datetime.now(
                            ).strftime('%Y-%m-%d_%H-%M-%S')+'.log'),
                            filemode='a')
        return_dict = {}
        if self.config['spec']['uploader']['clips']['upload_clips']:
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
                    desc=self.config['spec']['uploader']['clips']['desc'].format(
                        date=datestr),
                ))

            avid, bvid = self.uploader.upload(
                parts=output_parts,
                copyright=2,
                title=self.config['spec']['uploader']['clips']['title'].format(
                    date=datestr),
                tid=self.config['spec']['uploader']['clips']['tid'],
                tag=",".join(self.config['spec']['uploader']['clips']['tags']),
                desc=self.config['spec']['uploader']['clips']['desc'].format(
                    date=datestr),
                source="https://live.bilibili.com/"+self.room_id,
                thread_pool_workers=self.config['root']['uploader']['thread_pool_workers'],
                max_retry=self.config['root']['uploader']['max_retry'],
            )
            print(avid, bvid)
            return_dict["clips"] = {
                "avid": avid,
                "bvid": bvid
            }
        if self.config['spec']['uploader']['record']['upload_record']:
            splits_parts = []
            datestr = datetime.datetime.strptime(
                global_start, '%Y-%m-%d_%H-%M-%S').strftime('%Y{y}%m{m}%d{d}').format(y='年', m='月', d='日')
            filelists = os.listdir(self.splits_dir)
            for filename in filelists:
                if os.path.getsize(os.path.join(self.splits_dir, filename)) < 1024*1024:
                    continue
                title = filename
                splits_parts.append(VideoPart(
                    path=os.path.join(self.splits_dir, filename),
                    title=title,
                    desc=self.config['spec']['uploader']['record']['desc'].format(
                        date=datestr),
                ))

            avid, bvid = self.uploader.upload(
                parts=splits_parts,
                copyright=2,
                title=self.config['spec']['uploader']['record']['title'].format(
                    date=datestr),
                tid=self.config['spec']['uploader']['record']['tid'],
                tag=",".join(self.config['spec']
                             ['uploader']['record']['tags']),
                desc=self.config['spec']['uploader']['record']['desc'].format(
                    date=datestr),
                source="https://live.bilibili.com/"+self.room_id,
                thread_pool_workers=self.config['root']['uploader']['thread_pool_workers'],
                max_retry=self.config['root']['uploader']['max_retry'],
            )
            print(avid, bvid)
            return_dict["record"] = {
                "avid": avid,
                "bvid": bvid
            }
        return return_dict
