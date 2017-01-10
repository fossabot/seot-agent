import msgpack


def encode(data):
    return msgpack.packb(data, use_bin_type=True)


def decode(data):
    return msgpack.unpackb(data, encoding="utf-8")
