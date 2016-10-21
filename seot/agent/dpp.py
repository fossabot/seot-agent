import collections

import msgpack


def _encode_str(data):
    if isinstance(data, str):
        return data.encode("utf-8")
    elif isinstance(data, collections.Mapping):
        return dict(map(_encode_str, data.items()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(_encode_str, data))
    else:
        return data


def _decode_str(data):
    if isinstance(data, bytes):
        return data.decode("utf-8")
    elif isinstance(data, collections.Mapping):
        return dict(map(_decode_str, data.items()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(_decode_str, data))
    else:
        return data


def encode(data):
    return msgpack.packb(_encode_str(data))


def decode(data):
    return _decode_str(msgpack.unpackb(data))
