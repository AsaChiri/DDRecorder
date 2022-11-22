# DDRecorder

 Headless 全自动 B 站直播录播、切片、上传一体工具
 
**>=1.1.2 版本增加了自动检查更新功能，需要连接至 Github 服务器，敬请留意。**


## 感谢
FortuneDayssss/BilibiliUploader
MoyuScript/bilibili-api
ForgQi/biliup-rs
fastnlp/fastHan

## 参考文献
```
@inproceedings{geng-etal-2021-fasthan,
  author = {Geng, Zhichao and Yan, Hang and Qiu, Xipeng and Huang, Xuanjing},
  title = {fastHan: A BERT-based Multi-Task Toolkit for Chinese NLP},
  booktitle = {Proceedings of the 59th Annual Meeting of the Association for Computational Linguistics and the 11th International Joint Conference on Natural Language Processing: System Demonstrations},
  year = {2021},
  pages = {99--106}, 
  url = {https://aclanthology.org/2021.acl-demo.12}
}
```

## 安装指南（Windows）
1. 在 Release 下载 zip 包解压。
2. 修改配置文件 config.json 可以选择使用自带的 DDRecorderConfigManager（源码：AsaChiri/DDRecorderConfigManager)
3. 双击运行 DDRecorder.exe（这将使用 config.json）或 DDRecorder.exe <配置文件> 


## 安装指南（MacOS/Linux）
1. 安装 Python >= 3.8 https://www.python.org/downloads/release/python-3104/
2. 安装 ffmpeg https://ffmpeg.org/download.html
3. 执行 pip install -r requirements.txt
4. 修改 config 文件夹下的配置文件 config.json
5. 执行 python main.py <配置文件> 
   
## 配置文件字段解释

### 关于登录

**由于 B 站风控原因，账号密码登录失败（被风控）的可能性极高，建议获取 access_token，refresh_token 和 cookies 项目填入配置文件中；目前推荐使用 [biliup-rs](https://github.com/ForgQi/biliup-rs) 进行一次登录获取 access_token，refresh_token 和 cookies 项目后填入配置文件中。如果您使用 DDRecorderConfigManager，则相应功能已经集成。**

### 关于占位符
目前可以在配置文件里使用的占位符如下：
- {date} ：日期（格式为“2022 年 02 月 02 日”）
- {room_name} ：**最近的**直播间标题
- {year},{month},{day},{hour},{minute},{second}：直播开始时间的年、月、日、时、分、秒
- {rough_time}：直播开始时间的大概描述（凌晨、上午、下午、晚上）

### 关于手动切片
手动切片功能类似于 Nvidia 的 ShadowPlay 功能，在配置文件中的"manual_clipper"部分可以找到手动切片器相关设置。

在启用相关功能并指定接受指令的用户 UID，该用户可以在直播时发送特定弹幕来控制 DDRecorder 进行切片。

特定弹幕格式为```/DDR clip <回溯时间（秒）> [描述文本]```。其中描述文本可选，如果不指定描述文本，将会自动设置一个“手动切片_{编号}”的表述文本。

比如说，如果想要截取当前时间向前 5 分钟的内容，只需要发送```/DDR clip 300```。

如果想要指定描述文本为“主播锐评 ylg”，发送```/DDR clip 60 主播锐评ylg```即可。

手动切片的将会输出到与自动切片相同的文件夹，因此受到 uploader-clippers 中的设置项控制。即如果打开了自动上传切片功能，手动切片同样也会上传，不过分 P 名将不再是自动采集的弹幕关键词，而是上面所述的描述文本。

### 全局设置（root 部分）
- check_interval: 直播间开播状态检查间隔，单位为秒，每个监控直播间单独计数，因此如果监控直播间较多，建议适当调大。由于 B 站 API 访问次数限制，建议不要小于 30。默认：100
- print_interval：控制台消息打印间隔，单位为秒。
- data_path: 数据文件路径。默认："./"（即程序所在路径）
- logger: 日志相关设置
  - log_path: 日志文件路径。默认："./log"
  - log_level: 日志级别，可选 DEBUG\INFO\WARN
- request_header: 请求时使用的头。代码中已经包含了一个默认的，在这里进行调整将会覆盖默认值，如无必要请留空。
- uploader: 上传器相关设置
  <!-- - upload_by_edit：通过编辑稿件的方法上传多 P 切片，可以让后续分 P 上传时让前面的分 P 进入审核队列，加快开放浏览的速度。**请注意打开此功能时，请保持 keep_record_after_upload 和 keep_clippers_after_upload 为 True。否则，keep_record_after_upload 和 keep_clippers_after_upload 设置项将无效。**
  - thread_pool_workers: 上传时的线程池大小。默认：1
  - max_retry: 最大重试次数。默认：10 -->
  - lines: 上传使用的线路，可以选择 bda2, kodo, ws, qn, cos, cos-internal(支持腾讯云内网免流 + 提速)
- enable_baiduyun：是否开启百度云功能。

### 直播间特定设置（spec 部分，此部分是一个数组，如果需要同时监控多个直播间，依次添加至数组中即可）
- room_id: 房间号
- recorder: 录制器相关设置
  - keep_raw_record: 是否保留原始录像（flv）文件（录制器最后会合并所有 flv 文件导出 mp4）。默认：true
- parser: 弹幕分析器相关设置
  - interval: 弹幕计数间隔，单位秒。默认：30.
  - up_ratio: 开始切片位置弹幕数量与上一个时段弹幕数量之比的阈值。默认：2.5
  - down_ratio: 结束切片位置弹幕数量与上一个时段弹幕数量之比的阈值。默认：0.75
  - topK: 提取弹幕关键词的数量。默认：5
- clipper: 切片器相关设置
  - enable_clipper: 启用切片功能。默认：true
  - min_length: 切片最短长度，单位秒。默认：60
  - start_offset: 切片开始时间偏移量，正为向后偏移，负为向前偏移，单位秒。默认：0。建议根据直播间弹幕延迟调整。
  - end_offset: 切片结束时间偏移量，正为向后偏移，负为向前偏移，单位秒。默认：0。建议根据直播间弹幕延迟调整。
- manual_clipper: 手动切片器相关设置
  - enabled：启用手动切片器功能。默认：false
  - uid：手动切片器接受指令的用户 UID。
  - command: 自定义手动切片触发指令。
- uploader: 上传器相关设置
  - account: 上传账户信息
    - username: 用户名
    - password: 密码
    - access_token: Access token 
    - refresh_token: Refresh token
    - cookies:
      - SESSDATA: your SESSDATA
      - bili_jct: your bili_jct
      - DedeUserID: your DedeUserID
      - DedeUserID__ckMd5: your DedeUserID__ckMd5
      - sid: your sid
  - copyright: 稿件类型（1：自制，2：转载）**警告！未经授权投稿“自制”可能导致稿件无法通过审核！**
  - record: 录播上传设置
    - upload_record: 是否上传录播。默认：true
    - keep_record_after_upload: 是否在上传过审后保留录播。默认：true
    - split_interval: 录播划分间隔，单位秒。由于 B 站无法一次上传大文件，因此长录播需要分片才能上传。默认：3600。**如设为 0，表示不划分，如此请保证账号具有上传超大文件权限。**
    - title：上传视频的标题，可以使用占位符。
    - tid：分区编号，可在 https://github.com/FortuneDayssss/BilibiliUploader/wiki/Bilibili%E5%88%86%E5%8C%BA%E5%88%97%E8%A1%A8 查询
    - tags：上传视频的标签
    - desc：上传视频的描述，可以使用占位符。
    - cover：上传视频使用的封面文件路径。
  - clippers: 切片上传设置
    - upload_clippers: 是否上传切片。默认：true
    - keep_clippers_after_upload: 是否在上传过审后保留切片。默认：true
    - title：上传视频的标题，可以使用占位符。
    - tid：分区编号，可在 https://github.com/FortuneDayssss/BilibiliUploader/wiki/Bilibili%E5%88%86%E5%8C%BA%E5%88%97%E8%A1%A8 查询
    - tags：上传视频的标签
    - desc：上传视频的描述，可以使用占位符。
    - cover：上传视频使用的封面文件路径。
- backup：是否将录像备份到百度云。

## 已知问题
- record 文件夹下产生大量空文件夹。（Work-around patch）
- 自动上传无法登录，电磁力不足无法投稿分 P 稿件。（已更新）
- 被 B 站风控系统 412 后会无法工作。（预期下个功能更新优化。）
- PK 导致分辨率不正确出现花屏。（正在调查。）

## 预期更新
- 弹幕 jsonl 转为 ass 字幕并自动压入录播文件的功能。（预期下个功能更新。）
- 不上传百度也会在切片和或录播上传完成后删去 merge 文件的功能。（_预期下个功能更新。说实话不是很想加这个功能，可能这就是仓鼠症患者吧……_）
- 增加斗鱼、Twitch 和油管支持。（预期当前功能稳定后加入。）
