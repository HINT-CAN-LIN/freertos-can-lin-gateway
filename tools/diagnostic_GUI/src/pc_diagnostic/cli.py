import argparse
from contextlib import ExitStack
import math
import json
import sys

from .dbc_codec import DbcCodec
from .dbc_loader import DbcLoader
from .decode_service import DecodeService
from .frame import RawCanFrame
from .interfaces import CanInterfaceError, MockCanInterface, PythonCanInterface
from .logger import RawCanLogger, read_jsonl
from .monitor import capture, format_frame
from .sender import RawCanSender


def positive_int(value):
    result = int(value)
    if result <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return result


def seconds(value):
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise argparse.ArgumentTypeError("must be finite and nonnegative")
    return result


def parser():
    root = argparse.ArgumentParser(description="Classic CAN diagnostics: raw or explicit DBC mode")
    commands = root.add_subparsers(dest="command", required=True)
    encode = commands.add_parser("encode", help="DBC encode to raw JSON; does not send")
    encode.add_argument("--dbc", required=True, help="explicit DBC path (no default)")
    encode.add_argument("--message", required=True)
    encode.add_argument("--signals", required=True, help="JSON object of scaled values/DBC choice labels")
    for command in ("monitor", "log", "send", "decode"):
        sub = commands.add_parser(command)
        sub.add_argument("--backend", choices=("mock", "python-can"), default="mock")
        sub.add_argument("--interface", help="explicit python-can backend name")
        channel = sub.add_mutually_exclusive_group()
        channel.add_argument("--channel", help="string channel name")
        channel.add_argument("--channel-index", type=int, help="integer channel for indexed devices")
        sub.add_argument("--bitrate", type=positive_int, help="explicit nominal bitrate in bit/s")
        if command == "decode":
            sub.add_argument("--dbc", required=True, help="explicit DBC path (no default)")
        if command != "send":
            sub.add_argument("--input", help="mock JSONL frames; no timing replay")
            sub.add_argument("--count", type=positive_int)
            sub.add_argument("--duration", type=seconds, help="wall-clock seconds; bounds idle captures")
        if command == "log":
            sub.add_argument("--output", required=True, help="new capture file; existing files refused")
            sub.add_argument("--format", choices=("jsonl", "csv"), default="jsonl")
        if command == "send":
            sub.add_argument("--id", required=True, type=lambda s: int(s, 0), help="integer or 0x-prefixed ID")
            sub.add_argument("--data", default="", help="hex payload, e.g. space-separated bytes")
            sub.add_argument("--dlc", type=int, help="defaults to payload length; explicit for RTR")
            sub.add_argument("--extended", action="store_true")
            sub.add_argument("--rtr", action="store_true")
            sub.add_argument("--timeout", type=seconds, default=1.0, help="send submission timeout (seconds)")
    return root


def main(argv=None) -> int:
    arg_parser = parser()
    args = arg_parser.parse_args(argv)
    if args.command == "encode":
        try:
            loader = DbcLoader().load(args.dbc)
            frame = DbcCodec(loader).encode(args.message, json.loads(args.signals))
            print(json.dumps(frame.to_record(), ensure_ascii=False, allow_nan=False))
            return 0
        except (ValueError, OSError) as exc:
            print(f"can-diag: {exc}", file=sys.stderr)
            return 1
    channel = args.channel_index if args.channel_index is not None else args.channel
    if args.backend == "mock" and any(x is not None for x in (args.interface, channel, args.bitrate)):
        arg_parser.error("mock does not accept hardware connection settings")
    if args.backend == "python-can":
        if not args.interface or channel is None or channel == "":
            arg_parser.error("python-can requires --interface and --channel or --channel-index")
        if args.interface != "virtual" and args.bitrate is None:
            arg_parser.error("hardware backend requires explicit --bitrate")
        if getattr(args, "input", None):
            arg_parser.error("--input is only for mock")
    try:
        # Validate all user frames before opening a bus or creating a log.
        service = None
        if args.command == "decode":
            service = DecodeService(DbcCodec(DbcLoader().load(args.dbc)))
        frame = None
        if args.command == "send":
            if args.rtr and args.dlc is None:
                raise ValueError("RTR send requires explicit --dlc")
            frame = RawCanFrame(args.id, bytes.fromhex(args.data), dlc=args.dlc,
                                is_extended_id=args.extended, is_remote_frame=args.rtr, is_rx=False)
        frames = list(read_jsonl(args.input)) if getattr(args, "input", None) else []
        if args.backend == "mock" and args.command != "send":
            if args.count is None and args.duration is None:
                if not frames:
                    raise ValueError("empty mock requires --duration or a nonempty --input")
                args.count = len(frames)
            if args.duration is None and args.count > len(frames):
                raise ValueError("mock --count exceeds fixture length; use --duration to bound waiting")
        with ExitStack() as stack:
            transport = stack.enter_context(
                MockCanInterface(frames) if args.backend == "mock" else
                PythonCanInterface(interface=args.interface, channel=channel, bitrate=args.bitrate)
            )
            if args.command == "send":
                RawCanSender(transport).send(frame, timeout=args.timeout)
                label = "MOCK RECORDED" if args.backend == "mock" else "SUBMITTED (ECU receipt not verified)"
                print(f"{label}: {format_frame(frame)}")
            else:
                if args.command == "log":
                    logger = stack.enter_context(RawCanLogger(args.output, format=args.format))
                    callback = logger.write
                elif args.command == "decode":
                    def callback(value):
                        message = service.process(value)
                        print(json.dumps(message.to_record(), ensure_ascii=False, allow_nan=False), flush=True)
                else:
                    callback = lambda value: print(format_frame(value), flush=True)
                total = capture(transport, callback, count=args.count, duration=args.duration)
                print(f"Captured {total} frame(s) [{args.backend}]", file=sys.stderr)
        return 0
    except KeyboardInterrupt:
        print("Interrupted; resources closed.", file=sys.stderr)
        return 130
    except (ValueError, OSError, CanInterfaceError) as exc:
        print(f"can-diag: {exc}", file=sys.stderr)
        return 1
