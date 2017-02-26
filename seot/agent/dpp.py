import collections
import json

import msgpack

from pygments import formatters, highlight, lexers


def encode(data):
    return msgpack.packb(data, use_bin_type=True)


def decode(data):
    return msgpack.unpackb(data, encoding="utf-8")


def _sanitize(data):
    if isinstance(data, str):
        return data
    if isinstance(data, bytes):
        return "<binary data ({0} bytes)>".format(len(data))
    elif isinstance(data, collections.Mapping):
        return dict(map(_sanitize, data.items()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(_sanitize, data))
    else:
        return data


def format(data):
    formatted_json = json.dumps(_sanitize(data), indent=4)
    colorful_json = highlight(formatted_json, lexers.JsonLexer(),
                              formatters.TerminalFormatter())

    return colorful_json.strip()
