import copy
import datetime

import os
import re
import subprocess
from typing import Dict, List, Tuple
import logging
import jieba
import jieba.analyse
import ffmpeg
import utils
from BiliLive import BiliLive


def __parse_line(txt: str) -> Tuple[datetime.datetime, str]:
    time = re.match(r'\[(.*?)\](.*)', txt).group(1)
    text = re.match(r'\[(.*?)\](.*)', txt).group(2)
    return datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S'), text


def parse_lines(lines: List[str]) -> Dict[datetime.datetime, List[str]]:
    return_dict = {}
    for line in lines:
        time, text = __parse_line(line)
        if return_dict.get(time, None) is None:
            return_dict[time] = [text]
        else:
            return_dict[time].append(text)
    return return_dict


def get_cut_points(time_dict: Dict[datetime.datetime, List[str]], up_ratio: float = 2, down_ratio: float = 0.75, topK: int = 5) -> List[Tuple[datetime.datetime, datetime.datetime, List[str]]]:
    status = 0
    cut_points = []
    prev_num = None
    start_time = None
    temp_texts = []
    for time, texts in time_dict.items():
        if prev_num is None:
            start_time = time
            temp_texts = copy.copy(texts)
        elif status == 0 and len(texts) >= prev_num*up_ratio:
            status = 1
            temp_texts.extend(texts)
        elif status == 1 and len(texts) < prev_num*down_ratio:
            tags = jieba.analyse.extract_tags(
                ";".join(temp_texts), topK=topK, withWeight=False)
            cut_points.append((start_time, time, tags))
            status = 0
            start_time = time
            temp_texts = copy.copy(texts)
        elif status == 0:
            start_time = time
            temp_texts = copy.copy(texts)
        prev_num = len(texts)
    return cut_points


def get_true_timestamp(video_times: List[Tuple[datetime.datetime, float]], point: datetime.datetime) -> float:
    time_passed = 0
    for t, d in video_times:
        if point < t:
            return time_passed
        elif point - t <= datetime.timedelta(seconds=d):
            return time_passed + (point - t).total_seconds()
        else:
            time_passed += d
    return time_passed


def count(danmus: Dict[datetime.datetime, List[str]], live_start: datetime.datetime, live_duration: float, interval: int = 60) -> Dict[datetime.datetime, List[str]]:
    return_dict = {}
    clippers = (int(live_duration) // interval)+1
    for i in range(clippers):
        return_dict[live_start+datetime.timedelta(seconds=i*interval)] = []
    for time, text in danmus.items():
        delta = int((time - live_start).total_seconds())
        pos_time = (delta // interval) * interval
        key_time = live_start + datetime.timedelta(seconds=pos_time)
        if return_dict.get(key_time, None) is None:
            return_dict[key_time] = text
        else:
            return_dict[key_time].extend(text)
    return return_dict


def flv2ts(input_file: str, output_file: str, ffmpeg_path: str = "ffmpeg") -> subprocess.CompletedProcess:
    ret = subprocess.run(
        f"{ffmpeg_path} -y -fflags +discardcorrupt -i {input_file} -c copy -bsf:v h264_mp4toannexb -f mpegts {output_file}", shell=True, check=True)
    return ret


def concat(merge_conf_path: str, merged_file_path: str, ffmpeg_path: str = "ffmpeg") -> subprocess.CompletedProcess:
    ret = subprocess.run(
        f"{ffmpeg_path} -y -f concat -safe 0 -i {merge_conf_path} -c copy -fflags +igndts -avoid_negative_ts make_zero {merged_file_path}", shell=True, check=True)
    return ret


def get_start_time(filename: str) -> datetime.datetime:
    base = os.path.splitext(filename)[0]
    return datetime.datetime.strptime(
        " ".join(base.split("_")[1:3]), '%Y-%m-%d %H-%M-%S')


class Processor(BiliLive):
    def __init__(self, config: Dict, record_dir: str, danmu_path: str):
        super().__init__(config)
        self.record_dir = record_dir
        self.danmu_path = danmu_path
        self.global_start = utils.get_global_start_from_records(
            self.record_dir)
        self.merge_conf_path = utils.get_merge_conf_path(
            self.room_id, self.global_start, config['root']['global_path']['data_path'])
        self.merged_file_path = utils.get_mergd_filename(
            self.room_id, self.global_start, config['root']['global_path']['data_path'])
        self.outputs_dir = utils.init_outputs_dir(
            self.room_id, self.global_start, config['root']['global_path']['data_path'])
        self.splits_dir = utils.init_splits_dir(
            self.room_id, self.global_start, self.config['root']['global_path']['data_path'])
        self.times = []
        self.live_start = self.global_start
        self.live_duration = 0
        logging.basicConfig(level=utils.get_log_level(config),
                            format='%(asctime)s %(thread)d %(threadName)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S',
                            filename=os.path.join(config['root']['logger']['log_path'], datetime.datetime.now(
                            ).strftime('%Y-%m-%d_%H-%M-%S')+'.log'),
                            filemode='a')

    def pre_concat(self) -> None:
        filelist = os.listdir(self.record_dir)
        with open(self.merge_conf_path, "w", encoding="utf-8") as f:
            for filename in filelist:
                if os.path.splitext(
                        os.path.join(self.record_dir, filename))[1] == ".flv" and os.path.getsize(os.path.join(self.record_dir, filename)) > 1024*1024:
                    ts_path = os.path.splitext(os.path.join(
                        self.record_dir, filename))[0]+".ts"
                    _ = flv2ts(os.path.join(
                        self.record_dir, filename), ts_path, self.config['root']['global_path']['ffmpeg_path'])
                    if not self.config['spec']['recorder']['keep_raw_record']:
                        os.remove(os.path.join(self.record_dir, filename))
                    # ts_path = os.path.join(self.record_dir, filename)
                    duration = float(ffmpeg.probe(ts_path)[
                                     'format']['duration'])
                    start_time = get_start_time(filename)
                    self.times.append((start_time, duration))
                    f.write(
                        f"file '{ts_path}'\n")
        _ = concat(self.merge_conf_path, self.merged_file_path,
                   self.config['root']['global_path']['ffmpeg_path'])
        self.times.sort(key=lambda x: x[0])
        self.live_start = self.times[0][0]
        self.live_duration = (
            self.times[-1][0]-self.times[0][0]).total_seconds()+self.times[-1][1]

    def __cut_vedio(self, outhint: List[str], start_time: int, delta: int) -> subprocess.CompletedProcess:
        output_file = os.path.join(
            self.outputs_dir, f"{self.room_id}_{self.global_start.strftime('%Y-%m-%d_%H-%M-%S')}_{start_time:012}_{outhint}.mp4")
        cmd = f'ffmpeg -y -ss {start_time} -t {delta} -accurate_seek -i "{self.merged_file_path}" -c copy -avoid_negative_ts 1 "{output_file}"'
        ret = subprocess.run(cmd, shell=True, check=True)
        return ret

    def cut(self, cut_points: List[Tuple[datetime.datetime, datetime.datetime, List[str]]], min_length: int = 60) -> None:
        for cut_start, cut_end, tags in cut_points:
            start = get_true_timestamp(self.times,
                                       cut_start) + self.config['spec']['clipper']['start_offset']
            end = get_true_timestamp(self.times,
                                     cut_end) + self.config['spec']['clipper']['end_offset'] - self.config['spec']['clipper']['start_offset']
            delta = end-start
            outhint = " ".join(tags)
            if delta >= min_length:
                self.__cut_vedio(outhint, max(
                    0, int(start)), int(delta))

    def split(self, split_interval: int = 3600) -> None:
        if split_interval <= 0:
            split_interval = 3600
        duration = float(ffmpeg.probe(self.merged_file_path)
                         ['format']['duration'])
        num_splits = int(duration) // split_interval + 1
        for i in range(num_splits):
            output_file = os.path.join(
                self.splits_dir, f"{self.room_id}_{self.global_start.strftime('%Y-%m-%d_%H-%M-%S')}_{i}.mp4")
            cmd = f'ffmpeg -y -ss {i*split_interval} -t {split_interval} -accurate_seek -i "{self.merged_file_path}" -c copy -avoid_negative_ts 1 "{output_file}"'
            _ = subprocess.run(cmd, shell=True, check=True)

    def run(self) -> None:
        self.pre_concat()
        if not self.config['spec']['recorder']['keep_raw_record']:
            utils.del_files_and_dir(self.record_dir)
        # duration = float(ffmpeg.probe(self.merged_file_path)[
        #                              'format']['duration'])
        # start_time = get_start_time(self.merged_file_path)
        # self.times.append((start_time, duration))
        # self.live_start = self.times[0][0]
        # self.live_duration = (
        #     self.times[-1][0]-self.times[0][0]).total_seconds()+self.times[-1][1]

        with open(self.danmu_path, "r",encoding="utf-8") as f:
            lines = f.readlines()
        if self.config['spec']['clipper']['enable_clipper']:
            raw_danmu_dict = parse_lines(lines)
            counted_danmu_dict = count(
                raw_danmu_dict, self.live_start, self.live_duration, self.config['spec']['parser']['interval'])
            cut_points = get_cut_points(counted_danmu_dict, self.config['spec']['parser']['up_ratio'],
                                        self.config['spec']['parser']['down_ratio'], self.config['spec']['parser']['topK'])
            self.cut(cut_points, self.config['spec']['clipper']['min_length'])
        if self.config['spec']['uploader']['record']['upload_record']:
            self.split(self.config['spec']['uploader']
                       ['record']['split_interval'])
                       