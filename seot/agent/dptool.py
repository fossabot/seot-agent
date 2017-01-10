import argparse
import json
import sys

from pygments import formatters, highlight, lexers

import zmq

from .dpp import decode, encode


def read(args):
    ctx = zmq.Context()

    sock = ctx.socket(zmq.PULL)
    sock.bind(args.address)

    while True:
        data = decode(sock.recv())
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
    sock.send(encode(obj))


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
