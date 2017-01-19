import socket

import msgpack


SOCK_PATH = "/tmp/seot.sock"


def encode(data):
    return msgpack.packb(data, use_bin_type=True)


def decode(data):
    return msgpack.unpackb(data, encoding="utf-8")


def run_handler(handler):
    unpacker = msgpack.Unpacker(encoding="utf-8")

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(SOCK_PATH)

        while True:
            buf = sock.recv(1024)
            unpacker.feed(buf)
            for msg in unpacker:
                output = handler(msg)
                sock.send(encode(output))
