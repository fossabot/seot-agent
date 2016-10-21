import argparse
import collections
import json
import sys

import msgpack
from pygments import formatters, highlight, lexers
import zmq


def _encode(data):
    if isinstance(data, str):
        return data.encode("utf-8")
    elif isinstance(data, collections.Mapping):
        return dict(map(_encode, data.items()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(_encode, data))
    else:
        return data


def _decode(data):
    if isinstance(data, bytes):
        return data.decode("utf-8")
    elif isinstance(data, collections.Mapping):
        return dict(map(_decode, data.items()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(_decode, data))
    else:
        return data


def read(args):
    ctx = zmq.Context()

    sock = ctx.socket(zmq.PULL)
    sock.bind(args.address)

    while True:
        data = _decode(msgpack.unpackb(sock.recv()))
        formatted_json = json.dumps(data, indent=4)
        colorful_json = highlight(formatted_json, lexers.JsonLexer(),
                                  formatters.TerminalFormatter())
        print(colorful_json.strip())


def write(args):
    ctx = zmq.Context()

    sock = ctx.socket(zmq.PUSH)
    sock.connect(args.address)

    s = sys.stdin.read()
    obj = json.loads(s)
    sock.send(msgpack.packb(_encode(obj)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("address", type=str, help="ZMQ socket address")
    parser.add_argument("-r", "--read", action="store_true", help="Write mode")
    parser.add_argument("-w", "--write", action="store_true", help="Read mode")

    args = parser.parse_args()

    if not args.read and not args.write:
        args.read = True

    if args.read:
        read(args)
    elif args.write:
        write(args)
    else:
        read(args)

if __name__ == "__main__":
    main()
