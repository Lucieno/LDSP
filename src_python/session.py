# https://stackoverflow.com/questions/3207219/how-do-i-list-all-files-of-a-directory

from os import listdir, mkdir
from os.path import join, isfile, isdir, exists
from random import randint
import json

from src_python.config import Config, ExpConfig


def create_session():
    cur_sid = [int(f) for f in listdir(Config.running_data_path) if isdir(f)]
    sid = randint(1, Config.sid_max)
    while sid in cur_sid:
        sid = randint(1, Config.sid_max)
    hexsid = hex(sid)
    with open(join(Config.running_data_path, Config.cur_sid_file_name), 'w') as f:
        f.write(hexsid)
    mkdir(join(Config.running_data_path, hexsid))
    print(f"Created SID: {hexsid}")


cache_cur_sid = None


def read_current_sid(is_forced=False):
    global cache_cur_sid
    if cache_cur_sid is not None and is_forced is False:
        return cache_cur_sid
    with open(join(Config.running_data_path, Config.cur_sid_file_name), 'r') as f:
        sid = f.read()
    cache_cur_sid = int(sid, 16)
    return cache_cur_sid


def get_store_path(name, suffix=".json"):
    hexsid = hex(read_current_sid())
    return join(Config.running_data_path, hexsid, str(name) + suffix)


def is_store_path_exist(name):
    return exists(get_store_path(name))


# https://stackoverflow.com/questions/3768895/how-to-make-a-class-json-serializable
def dumper(obj):
    # print("class name:", type(obj).__name__)
    # if '__attrs__' in dir(obj) and 'toJSON' in obj.__attrs__():
    #     print("using toJSON")
    #     return obj.toJSON()
    if 'to_json' in dir(obj):
        return obj.to_json()
    # elif type(obj).__name__ == 'bn128_FQ2':
    #     return dict(enumerate(obj.coeffs))
    elif '__dict__' in dir(obj):
        return obj.__dict__
    else:
        raise Exception("Yet to implement serialization", dir(obj), obj)


def store_obj(name, obj):
    out_json = json.dumps(obj, default=dumper)
    store_path = get_store_path(name)
    with open(get_store_path(name), 'w') as f:
        f.write(out_json)


def load_obj(name, cls_ptr):
    with open(get_store_path(name), 'r') as f:
        in_json = f.read()
    if cls_ptr == dict:
        return json.loads(in_json, object_hook=dict)
    elif 'to_json' in dir(cls_ptr):
        return cls_ptr.from_json(in_json)
    # elif cls_ptr.__name__ == 'bn128_FQ2':
    #     obj = cls_ptr()
    #     loaded = json.loads(in_json, object_hook=tuple)
    #     # print("loaded", loaded)
    #     obj.coeffs = loaded
    #     return obj
    elif '__dict__' in dir(cls_ptr):
        res = cls_ptr()
        res.__dict__ = json.loads(in_json, object_hook=dict)
        # print("dir(res)", dir(res))
        # print("res.__dict__", res.__dict__)
        return res
    else:
        raise Exception("Yet to implement deserialization", cls_ptr, dir(cls_ptr), json.loads(in_json))


# def load_dict(name):
#     with open(get_store_path(name), 'r') as f:
#         in_json = f.read()
#     return json.loads(in_json, object_hook=dict)

# def load_class_instance(name, class_pointer):
#     with open(get_store_path(name), 'r') as f:
#         in_json = f.read()
#     print(in_json)
#     return json.loads(in_json, object_hook=class_pointer)

def store_config():
    def dict_filter(d, f):
        return {k: v for k, v in d.items() if f(k, v)}

    def store_class(name, class_pointer):
        d = dict_filter(class_pointer.__dict__, lambda k, v: str(k).startswith("__") is False)
        store_obj(name, d)

    store_class("Config", Config)
    store_class("ExpConfig", ExpConfig)


if __name__ == "__main__":
    import os
    cwd = os.getcwd()
    print("Current working directory: {0}".format(cwd))

    create_session()
    print(hex(read_current_sid()))
    store_config()
