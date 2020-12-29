# DDRecoder
 Headless全自动B站直播录播、切片、上传一体工具

## 安装指南
1. 安装Python >= 3.7 https://www.python.org/downloads/release/python-386/
2. 安装ffmpeg https://ffmpeg.org/download.html
3. 执行pip install -r requirements.txt
4. 修改config文件夹下的配置文件，root_config.json是全局设置，config.spec.json是直播间特定设置
5. 执行python main.py <全局设置文件> <直播间特定设置文件> （如果需要录制多个直播间就开多个）
   
## 配置文件字段解释

### 全局设置
- check_interval: 直播间开播状态检查间隔，单位为秒。由于B站API访问次数限制，建议不要小于30。如果要多开，建议适当调大。默认：60
- global_path: 路径相关设置
  - data_path: 数据文件路径。默认："./"
  - ffmpeg_path: FFmpeg可执行文件路径，如果已经加入PATH中，填写"ffmpeg"即可。默认："ffmpeg"
- logger: 日志相关设置
  - log_path: 日志文件路径。默认："./log"
  - log_level: 日志级别，可选DEBUG\INFO\WARN
- request_header: 请求时使用的头。代码中已经包含了一个默认的，在这里进行调整将会覆盖默认值，如无必要请留空。
- uploader: 上传器相关设置
  - thread_pool_workers: 上传时的线程池大小。默认：1
  - max_retry: 最大重试次数。默认：10

### 直播间特定设置
- room_id: 房间号
- recorder: 录制器相关设置
  - keep_raw_record: 是否保留原始录像（flv）文件（录制器最后会合并所有flv文件导出mp4）。默认：true
- parser: 弹幕分析器相关设置
  - interval: 弹幕计数间隔，单位秒。默认：60.
  - up_ratio: 开始切片位置弹幕数量与上一个时段弹幕数量之比的阈值。默认：2.5
  - down_ratio:  结束切片位置弹幕数量与上一个时段弹幕数量之比的阈值。默认：0.75
  - topK: 提取弹幕关键词的数量。默认：5
- clipper: 切片器相关设置
  - enable_clipper: 启用切片功能。默认：true
  - min_length: 切片最短长度，单位秒。默认：60
  - before_offset: 切片开始时间偏移量，正为向后偏移，负为向前偏移，单位秒。默认：0。建议根据直播间弹幕延迟调整。
  - end_offset: 切片结束时间偏移量，正为向后偏移，负为向前偏移，单位秒。默认：0。建议根据直播间弹幕延迟调整。
- uploader: 上传器相关设置
  - account: 上传账户信息
    - username: 用户名
    - password: 密码
  - record: 录播上传设置
    - upload_record: 是否上传录播。默认：true
    - keep_record_after_upload: 是否在上传后保留录播。（此功能暂时不包含）默认：true
    - split_interval: 录播划分间隔，单位秒。由于B站无法一次上传大文件，因此长录播需要分片才能上传。默认：3600
    - title：上传视频的标题，可以用 {date} 标识录播日期
    - tid：分区编号，可在 https://github.com/FortuneDayssss/BilibiliUploader/wiki/Bilibili%E5%88%86%E5%8C%BA%E5%88%97%E8%A1%A8 查询
    - tags：上传视频的标签
    - desc：上传视频的描述，可以用 {date} 标识录播日期
  - clippers: 切片上传设置
    - upload_clippers: 是否上传切片。默认：true
    - keep_clippers_after_upload: 是否在上传后保留切片。（此功能暂时不包含）默认：true
    - title：上传视频的标题，可以用 {date} 标识录播日期
    - tid：分区编号，可在 https://github.com/FortuneDayssss/BilibiliUploader/wiki/Bilibili%E5%88%86%E5%8C%BA%E5%88%97%E8%A1%A8 查询
    - tags：上传视频的标签
    - desc：上传视频的描述，可以用 {date} 标识录播日期
