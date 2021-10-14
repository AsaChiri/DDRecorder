## BilibiliUploader
模拟B站pc投稿工具进行投稿

## B站分区tid号码查询

https://github.com/FortuneDayssss/BilibiliUploader/wiki/Bilibili%E5%88%86%E5%8C%BA%E5%88%97%E8%A1%A8

## 海外DNS无法解析问题

海外的DNS有时无法解析upcdn-szhw.bilivideo.com域名导致上传失败，此时可以考虑将DNS服务器临时改为1.2.4.8

## 登录

支持密码登录以及access_token登录

```
uploader = BilibiliUploader()

# 账号密码登录
uploader.login("username_example", "password_example")

# 使用存有access_token的json文件登录
uploader.login_by_access_token_file("/YOURFILEPATH/bililogin.json")

# 直接使用access_token登录，refresh_token可以不提供，没有refresh_token更新时间的话access_token会在获取的30天后过期(todo: refresh)
uploader.login_by_access_token("ACCESS_TOKEN")
uploader.login_by_access_token("ACCESS_TOKEN", "REFRESH_TOKEN")

# 登录后获取access_token与refresh_token
access_token, refresh_token = uploader.save_login_data(file_name="/YOURFOLDER/bililogin.json")
```

## Example
```
from bilibiliuploader.bilibiliuploader import BilibiliUploader
from bilibiliuploader.core import VideoPart

if __name__ == '__main__':
    uploader = BilibiliUploader()
    
    # 登录
    uploader.login("username_example", "password_example")

    # 处理视频文件
    parts = []
    parts.append(VideoPart(
        path="C:/Users/xxx/Videos/1.mp4",
        title="分p名:p1",
        desc="这里是p1的简介"
    ))
    parts.append(VideoPart(
        path="C:/Users/xxx/Videos/2.mp4",
        title="分p名:p2",
        desc="这里是p2的简介"
    ))
    
    # 上传
    avid, bvid = uploader.upload(
        parts=parts,
        copyright=2,
        title='py多p上传测试1',
        tid=171,
        tag=",".join(["python", "测试"]),
        desc="python多p上传测试",
        source='https://www.github.com/FortuneDayssss',
        thread_pool_workers=5,
    )
    
    
    # 修改已有投稿
    parts = []
    parts.append(VideoPart(
        path="C:/Users/xxx/Videos/1.mp4",
        title="edit分p名:p1",
        desc="这里是p1的简介"
    ))
    parts.append(VideoPart(
        path="C:/Users/xxx/Videos/2.mp4",
        title="edit分p名:p2",
        desc="这里是p2的简介"
    ))
    uploader.edit(
        avid=414167215,
        parts=parts,
        copyright=2,
        title='edit 测试1',
        tag=",".join(["python", "测试", "edit"]),
        desc="python多p edit测试",
        source='https://www.github.com/FortuneDayssss',
        cover='/cover_folder/cover.png',
    )
```

## Parameters && Structures

### VideoPart

VideoPart代表投稿内各个分p

* path:上传的文件路径

* title:分p标题

* desc:分p简介

* server_file_name:pre_upload API自动生成的服务端文件名，不需要填写


### Upload

* parts：VideoPart结构体

* copyright: int 版权标志，1为原创2为转载，转载投稿需要填写下面的source参数

* title: str 投稿标题

* tid: int 投稿分区号

* tag: str 以半角逗号分割的字符串

* desc: str 视频简介

* source: int, 转载地址

* cover: str, 封面图片路径，若路径不正确则默认封面为空

* no_reprint: int = 0,视频是否禁止转载标志0无1禁止

* open_elec: int = 1,是否开启充电面板，0为关闭1为开启

* max_retry: int = 5 上传重试次数

* thread_pool_workers: int = 1 多视频并行上传最大线程数，默认为串行上传


### Edit

* avid: av号 (av/bv提供其一即可)

* bvid: bv号 (av/bv提供其一即可)

* parts: VideoPart list (不填写参数则不修改)

* insert_index: 新视频分P位置(不填写参数则从最后追加)

* copyright: 原创/转载 (不填写参数则不修改)

* title: 投稿标题 (不填写参数则不修改)

* tid: 分区id (不填写参数则不修改)

* tag: 标签 (不填写参数则不修改)

* desc: 投稿简介 (不填写参数则不修改)

* source: 转载地址 (不填写参数则不修改)

* cover: 封面路径 (不填写参数则不修改)

* no_reprint: 可否转载 (不填写参数则不修改)

* open_elec: 充电 (不填写参数则不修改)

* max_retry: 上传重试次数

* thread_pool_workers: 多视频并行上传最大线程数，默认为串行上传


## reference
[记一次B站投稿工具逆向](https://fortunedayssss.github.io/2020/05/20/%E8%AE%B0%E4%B8%80%E6%AC%A1B%E7%AB%99%E6%8A%95%E7%A8%BF%E5%B7%A5%E5%85%B7%E9%80%86%E5%90%91.html). 
