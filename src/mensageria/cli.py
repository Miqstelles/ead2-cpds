"""CLI do projeto.

Subcomandos:
  mensageria broker [--host H] [--port P] [--log-dir D]
  mensageria client --name NAME [--host H] [--port P]
                    [--register-only]
                    [--send-unicast TARGET MSG]
                    [--send-broadcast MSG]
                    [--consume]
                    [--repl]
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import Optional

from .broker import Broker
from .client import Client, ClientError


def _broker_main(args: argparse.Namespace) -> int:
    broker = Broker(host=args.host, port=args.port, log_dir=args.log_dir)
    host, port = broker.start()
    print(f"[broker] ouvindo em {host}:{port}", flush=True)
    print(f"[broker] logs em '{args.log_dir}/'", flush=True)
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n[broker] encerrando...", flush=True)
    finally:
        broker.stop()
    return 0


def _client_repl(client: Client) -> None:
    print("[client] REPL. Comandos:")
    print("  send <nome> <mensagem>      -> unicast")
    print("  cast <canal> <mensagem>     -> multicast")
    print("  bcast <mensagem>            -> broadcast")
    print("  sub <canal>                 -> subscrever em canal")
    print("  unsub <canal>               -> desinscrever")
    print("  consume [N]                 -> ler ate N mensagens")
    print("  quit                        -> encerrar")
    while True:
        try:
            line = input(f"{client.name}> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        parts = line.split(maxsplit=2)
        cmd = parts[0].lower()
        try:
            if cmd == "quit":
                break
            elif cmd == "send" and len(parts) == 3:
                r = client.send_unicast(parts[1], parts[2])
                print(f"  ok: {r}")
            elif cmd == "cast" and len(parts) == 3:
                r = client.send_multicast(parts[1], parts[2])
                print(f"  ok: {r}")
            elif cmd == "bcast" and len(parts) >= 2:
                payload = line.split(maxsplit=1)[1]
                r = client.send_broadcast(payload)
                print(f"  ok: {r}")
            elif cmd == "sub" and len(parts) >= 2:
                client.subscribe(parts[1])
                print("  ok")
            elif cmd == "unsub" and len(parts) >= 2:
                client.unsubscribe(parts[1])
                print("  ok")
            elif cmd == "consume":
                n: Optional[int] = None
                if len(parts) >= 2:
                    n = int(parts[1])
                msgs = client.consume(n)
                if not msgs:
                    print("  (sem mensagens)")
                for m in msgs:
                    print(
                        f"  [{m.lamport_produced}->{m.lamport_buffered}->{m.lamport_consumed}] "
                        f"{m.producer} {m.target_type}: {m.payload}"
                    )
            else:
                print("  comando desconhecido")
        except ClientError as e:
            print(f"  erro: {e}")


def _client_main(args: argparse.Namespace) -> int:
    client = Client(name=args.name, host=args.host, port=args.port)
    client.connect()
    try:
        client.register()
        print(f"[client] '{args.name}' registrado em {args.host}:{args.port}")
        if args.send_unicast:
            tgt, msg = args.send_unicast
            r = client.send_unicast(tgt, msg)
            print(f"unicast ok: {r}")
        if args.send_broadcast:
            r = client.send_broadcast(args.send_broadcast)
            print(f"broadcast ok: {r}")
        if args.consume:
            msgs = client.consume()
            for m in msgs:
                print(
                    f"[{m.lamport_produced}->{m.lamport_buffered}->{m.lamport_consumed}] "
                    f"{m.producer} {m.target_type}: {m.payload}"
                )
        if args.repl or not (args.send_unicast or args.send_broadcast or args.consume or args.register_only):
            _client_repl(client)
    finally:
        client.teardown()
        client.close()
    return 0


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(prog="mensageria")
    sub = parser.add_subparsers(dest="cmd", required=True)

    pb = sub.add_parser("broker", help="inicia o broker (Message Bus)")
    pb.add_argument("--host", default="127.0.0.1")
    pb.add_argument("--port", type=int, default=9000)
    pb.add_argument("--log-dir", default="logs")

    pc = sub.add_parser("client", help="inicia um cliente")
    pc.add_argument("--name", required=True)
    pc.add_argument("--host", default="127.0.0.1")
    pc.add_argument("--port", type=int, default=9000)
    pc.add_argument("--register-only", action="store_true")
    pc.add_argument("--send-unicast", nargs=2, metavar=("TARGET", "MSG"))
    pc.add_argument("--send-broadcast", metavar="MSG")
    pc.add_argument("--consume", action="store_true")
    pc.add_argument("--repl", action="store_true")

    args = parser.parse_args(argv)
    if args.cmd == "broker":
        return _broker_main(args)
    if args.cmd == "client":
        return _client_main(args)
    parser.error("subcomando invalido")
    return 2


if __name__ == "__main__":
    sys.exit(main())
