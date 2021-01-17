import asyncio
import datetime
import json
import logging
import os
import zlib

from aiowebsocket.converses import AioWebSocket

import utils
from BiliLive import BiliLive


class BiliDanmuRecorder(BiliLive):
    def __init__(self, config: dict, global_start: datetime.datetime):
        super().__init__(config)
        self.log_filename = utils.init_danmu_log_file(
            self.room_id, global_start, config['root']['global_path']['data_path'])
        self.room_server_api = 'wss://broadcastlv.chat.bilibili.com/sub'

    def __log_danmu(self, body: str) -> None:
        def preProcess(text, l=3):
            i = 0
            while i < len(text)-1:
                j = i+1
                while j < len(text) and text[j] == text[i]:
                    j += 1
                if j-i > l:
                    text = text[:i] + text[i]*l + text[j:]
                    i += l
                else:
                    i += 1
            return text
        with open(self.log_filename, 'a', encoding="utf-8") as fd:
            fd.write(datetime.datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'))
            fd.write(preProcess(body)+'\n')

    async def __send_heart_beat(self, websocket):
        hb = '00000010001000010000000200000001'
        while self.live_status:
            await asyncio.sleep(30)
            await websocket.send(bytes.fromhex(hb))
            logging.debug(self.generate_log("弹幕接收器已发送心跳包"))

    async def __receDM(self, websocket):
        while self.live_status:
            recv_text = await websocket.receive()
            self.__printDM(recv_text)

    async def __startup(self):
        data_raw = '000000{headerLen}0010000100000007000000017b22726f6f6d6964223a{roomid}7d'
        data_raw = data_raw.format(headerLen=hex(
            27+len(self.room_id))[2:], roomid=''.join(map(lambda x: hex(ord(x))[2:], list(self.room_id))))
        async with AioWebSocket(self.room_server_api) as aws:
            converse = aws.manipulator
            await converse.send(bytes.fromhex(data_raw))
            tasks = [self.__receDM(converse), self.__send_heart_beat(converse)]
            await asyncio.wait(tasks)

    def run(self):
        logging.basicConfig(level=utils.get_log_level(self.config),
                            format='%(asctime)s %(thread)d %(threadName)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S',
                            handlers=[logging.FileHandler(os.path.join(self.config['root']['logger']['log_path'], "DanmuRecoder_"+datetime.datetime.now(
                            ).strftime('%Y-%m-%d_%H-%M-%S')+'.log'), "a", encoding="utf-8")])
        try:
            asyncio.get_event_loop().run_until_complete(self.__startup())
        except KeyboardInterrupt:
            logging.info(self.generate_log("键盘指令退出"))

    def __printDM(self, data):
        # 获取数据包的长度，版本和操作类型
        packetLen = int(data[:4].hex(), 16)
        ver = int(data[6:8].hex(), 16)
        op = int(data[8:12].hex(), 16)
        # 有的时候可能会两个数据包连在一起发过来，所以利用前面的数据包长度判断，
        if len(data) > packetLen:
            self.__printDM(data[packetLen:])
            data = data[:packetLen]

        # 有时会发送过来 zlib 压缩的数据包，这个时候要去解压。
        if ver == 2:
            data = zlib.decompress(data[16:])
            self.__printDM(data)
            return

        # ver 为1的时候为进入房间后或心跳包服务器的回应。op 为3的时候为房间的人气值。
        if ver == 1:
            if op == 3:
                logging.debug(self.generate_log(
                    '[RENQI]  {}\n'.format(int(data[16:].hex(), 16))))
            return

        # ver 不为2也不为1目前就只能是0了，也就是普通的 json 数据。
        # op 为5意味着这是通知消息，cmd 基本就那几个了。
        if op == 5:
            try:
                jd = json.loads(data[16:].decode('utf-8', errors='ignore'))
                if jd['cmd'] == 'DANMU_MSG':
                    if jd['info'][1] != "":
                        self.__log_danmu(jd['info'][1])
                    logging.debug(self.generate_log(
                        f"[DANMU] {jd['info'][2][1]}: {jd['info'][1]}\n"))
                elif jd['cmd'] == 'SEND_GIFT':
                    logging.debug(self.generate_log(
                        f"[GIFT] {jd['data']['uname']} {jd['data']['action']} {jd['data']['num']} x {jd['data']['giftName']}\n"))
                elif jd['cmd'] == 'LIVE':
                    logging.info(self.generate_log(
                        '[Notice] LIVE Start!\n'))
                elif jd['cmd'] == 'PREPARING':
                    logging.info(self.generate_log(
                        '[Notice] LIVE Ended!\n'))
                elif jd['cmd'] == 'INTERACT_WORD':
                    logging.info(self.generate_log(
                        f"[Notice] UID:{jd['data']['uid']} Username:{jd['data']['uname']} enters the live room\n"))
                elif jd['cmd'] == 'SUPER_CHAT_MESSAGE':
                    if jd['info'][1] != "":
                        self.__log_danmu(jd['data']['message'])
                    logging.info(self.generate_log(
                        f"[Notice] UID:{jd['data']['uid']} sends a superchat:{jd['data']['message']}\n"))
                else:
                    logging.info(self.generate_log('[OTHER] '+jd['cmd']))
            except Exception as e:
                logging.error(self.generate_log(
                    'Error while parsing danmu data:'+str(e)))
