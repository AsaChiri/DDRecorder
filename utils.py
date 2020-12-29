import os
import datetime
import logging


def get_log_level(config: dict) -> int:
    if config['root']['logger']['log_level'] == 'DEBUG':
        return logging.DEBUG
    if config['root']['logger']['log_level'] == 'INFO':
        return logging.INFO
    if config['root']['logger']['log_level'] == 'WARN':
        return logging.WARN
    if config['root']['logger']['log_level'] == 'ERROR':
        return logging.ERROR


def check_and_create_dir(dirs: str):
    if not os.path.exists(dirs):
        os.mkdir(dirs)


def init_data_dirs(root_dir: str = os.getcwd()):
    check_and_create_dir(os.path.join(root_dir, 'data'))
    check_and_create_dir(os.path.join(root_dir, 'data', 'records'))
    check_and_create_dir(os.path.join(root_dir, 'data', 'merged'))
    check_and_create_dir(os.path.join(root_dir, 'data', 'merge_confs'))
    check_and_create_dir(os.path.join(root_dir, 'data', 'logs'))
    check_and_create_dir(os.path.join(root_dir, 'data', 'danmu'))
    check_and_create_dir(os.path.join(root_dir, 'data', 'outputs'))
    check_and_create_dir(os.path.join(root_dir, 'data', 'splits'))


def init_record_dir(room_id: str, global_start: datetime.datetime,root_dir: str = os.getcwd()) -> str:
    dirs = os.path.join(root_dir, 'data', 'records',
                        f"{room_id}_{global_start.strftime('%Y-%m-%d_%H-%M-%S')}")
    check_and_create_dir(dirs)
    return dirs


def init_danmu_log_file(room_id: str, global_start: datetime.datetime,root_dir: str = os.getcwd()) -> str:
    log_filename = os.path.join(
        root_dir, 'data', 'danmu', f"{room_id}_{global_start.strftime('%Y-%m-%d_%H-%M-%S')}_danmu.log")
    return log_filename


def generate_filename(room_id: str) -> str:
    return f"{room_id}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.flv"


def get_global_start_from_records(record_dir: str) -> datetime.datetime:
    base = os.path.basename(record_dir)
    return datetime.datetime.strptime(" ".join(base.split("_")[1:3]), '%Y-%m-%d %H-%M-%S')


def get_merge_conf_path(room_id: str, global_start: datetime.datetime, root_dir: str = os.getcwd()) -> str:
    filename=os.path.join(root_dir, 'data', 'merged',
                            f"{room_id}_{global_start.strftime('%Y-%m-%d_%H-%M-%S')}_merged.mp4")
    return filename


def init_outputs_dir(room_id: str, global_start: datetime.datetime, root_dir: str = os.getcwd()) -> str:
    dirs=os.path.join(root_dir, 'data', 'outputs',
                        f"{room_id}_{global_start.strftime('%Y-%m-%d_%H-%M-%S')}")
    check_and_create_dir(dirs)
    return dirs

def init_splits_dir(room_id: str, global_start: datetime.datetime, root_dir: str = os.getcwd()) -> str:
    dirs=os.path.join(root_dir, 'data', 'splits',
                        f"{room_id}_{global_start.strftime('%Y-%m-%d_%H-%M-%S')}")
    check_and_create_dir(dirs)
    return dirs

def get_mergd_filename(room_id: str, global_start: datetime.datetime, root_dir: str = os.getcwd()) -> str:
    filename = os.path.join(root_dir, 'data', 'merge_conf',
                            f"{room_id}_{global_start.strftime('%Y-%m-%d_%H-%M-%S')}_merge_conf.txt")
    return filename
