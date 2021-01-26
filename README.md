# DDRecorder
 Headless全自动B站直播录播、切片、上传一体工具
 
## 感谢
FortuneDayssss/BilibiliUploader

## 安装指南（Windows）
1. 在Release下载zip包解压。
2. 修改配置文件config.json
3. 双击运行DDRecorder.exe （这将使用config.json）或 DDRecorder.exe <配置文件> 

## 安装指南（MacOS/Linux）
1. 安装Python >= 3.7 https://www.python.org/downloads/release/python-386/
2. 安装ffmpeg https://ffmpeg.org/download.html
3. 执行pip install -r requirements.txt
4. 修改config文件夹下的配置文件config.json
5. 执行python main.py <配置文件> 
   
## 配置文件字段解释

### 全局设置（root部分）
- check_interval: 直播间开播状态检查间隔，单位为秒，每个监控直播间单独计数，因此如果监控直播间较多，建议适当调大。由于B站API访问次数限制，建议不要小于30。默认：100
- print_interval：控制台消息打印间隔，单位为秒。
- data_path: 数据文件路径。默认："./"（即程序所在路径）
- logger: 日志相关设置
  - log_path: 日志文件路径。默认："./log"
  - log_level: 日志级别，可选DEBUG\INFO\WARN
- request_header: 请求时使用的头。代码中已经包含了一个默认的，在这里进行调整将会覆盖默认值，如无必要请留空。
- uploader: 上传器相关设置
  - upload_by_edit：通过编辑稿件的方法上传多P切片，可以让后续分P上传时让前面的分P进入审核队列，加快开放浏览的速度
  - thread_pool_workers: 上传时的线程池大小。默认：1
  - max_retry: 最大重试次数。默认：10
- enable_baiduyun：是否开启百度云功能。

### 直播间特定设置（spec部分，此部分是一个数组，如果需要同时监控多个直播间，依次添加至数组中即可）
- room_id: 房间号
- recorder: 录制器相关设置
  - keep_raw_record: 是否保留原始录像（flv）文件（录制器最后会合并所有flv文件导出mp4）。默认：true
- parser: 弹幕分析器相关设置
  - interval: 弹幕计数间隔，单位秒。默认：30.
  - up_ratio: 开始切片位置弹幕数量与上一个时段弹幕数量之比的阈值。默认：2.5
  - down_ratio:  结束切片位置弹幕数量与上一个时段弹幕数量之比的阈值。默认：0.75
  - topK: 提取弹幕关键词的数量。默认：5
- clipper: 切片器相关设置
  - enable_clipper: 启用切片功能。默认：true
  - min_length: 切片最短长度，单位秒。默认：60
  - start_offset: 切片开始时间偏移量，正为向后偏移，负为向前偏移，单位秒。默认：0。建议根据直播间弹幕延迟调整。
  - end_offset: 切片结束时间偏移量，正为向后偏移，负为向前偏移，单位秒。默认：0。建议根据直播间弹幕延迟调整。
- uploader: 上传器相关设置
  - account: 上传账户信息
    - username: 用户名
    - password: 密码
  - record: 录播上传设置
    - upload_record: 是否上传录播。默认：true
    - keep_record_after_upload: 是否在上传过审后保留录播。默认：true
    - split_interval: 录播划分间隔，单位秒。由于B站无法一次上传大文件，因此长录播需要分片才能上传。默认：3600。如设为0，表示不划分，如此请保证账号具有超大文件权限。
    - title：上传视频的标题，可以用 {date} 标识日期
    - tid：分区编号，可在 https://github.com/FortuneDayssss/BilibiliUploader/wiki/Bilibili%E5%88%86%E5%8C%BA%E5%88%97%E8%A1%A8 查询
    - tags：上传视频的标签
    - desc：上传视频的描述，可以用 {date} 标识日期
  - clippers: 自动切片上传设置
    - upload_clippers: 是否上传自动切片。默认：true
    - keep_clippers_after_upload: 是否在上传过审后保留自动切片。默认：true
    - title：上传视频的标题，可以用 {date} 标识日期
    - tid：分区编号，可在 https://github.com/FortuneDayssss/BilibiliUploader/wiki/Bilibili%E5%88%86%E5%8C%BA%E5%88%97%E8%A1%A8 查询
    - tags：上传视频的标签
    - desc：上传视频的描述，可以用 {date} 标识日期
- backup：是否将录像备份到百度云。
