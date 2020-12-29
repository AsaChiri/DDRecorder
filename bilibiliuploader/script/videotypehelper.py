from bilibiliuploader.core import *
from bilibiliuploader.util import cipher

TYPE_INFO_ADDR = "http://member.bilibili.com/x/client/archive/pre"


def get_type_info(access_key):
    tag_get_data = {
        "access_key": access_key,
        "build": "1054"
    }

    tag_get_data["sign"] = cipher.sign_dict(tag_get_data, APPSECRET)

    r = requests.get(
        url=TYPE_INFO_ADDR,
        params=tag_get_data
    )

    data = r.json()["data"]

    typelist = data["typelist"]
    print(typelist)

    result = []

    for video_type_1 in typelist:
        vt1_str = "## {}: {}\n\n".format(video_type_1["id"], video_type_1["name"])
        if "children" in video_type_1:
            children = video_type_1["children"]
            children_list = []
            for video_type_2 in children:
                vt2_str = "{}: {}\n\n".format(video_type_2["id"], video_type_2["name"])
                children_list.append((video_type_2["id"], vt2_str))
            children_list.sort(key=lambda x: x[0])
            for i, s in children_list:
                vt1_str += s
        result.append((video_type_1["id"], vt1_str))
    result.sort(key=lambda x: x[0])

    for i, s in result:
        print(s)


# Script for simply generating markdown string about Bilibili video type
if __name__ == '__main__':
    get_type_info("YOUR_ACCESS_TOKEN")
