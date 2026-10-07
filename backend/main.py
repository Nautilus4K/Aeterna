from logger import *
from app import *
from ssl_manager import SSLManager

import argparse
import waitress
import threading
import os
import json
import bcrypt
import getpass
# import subprocess

parser = argparse.ArgumentParser(prog="Media-Server")
# parser.add_argument("-v", "--verbose", action="store_true", help="Console verbose loggings")
parser.add_argument("-t", "--threads", type=int, help="Thread count for this server")
parser.add_argument("-a", "--address", action="store", type=str, help="Address to host the website. Default 127.0.0.1")
parser.add_argument("-p", "--port", action="store", type=int, help="Port to host the website. Default 8000")
parser.add_argument("-u", "--users", action="store_true", help="Edit users settings")
# parser.add_argument("-d", "--disk", action="store", type=str, help="Target disk")
parser.add_argument("-s", "--ssl", action="store_true", help="Serve over HTTPS using an auto-renewing Let's Encrypt certificate")
parser.add_argument("--domain", action="store", type=str, default="nautilus4k.ddns.net", help="Domain name to request the SSL certificate for")
parser.add_argument("--email", action="store", type=str, help="Contact email for Let's Encrypt account (required with --ssl)")
parser.add_argument("--staging", action="store_true", help="Use Let's Encrypt's staging environment (for testing, avoids rate limits)")
args = parser.parse_args()

HOST = args.address if args.address is not None else "127.0.0.1"
PORT = args.port if args.port is not None else 8000
THREADCOUNT = args.threads if args.threads is not None else 4
USERSEDITMODE = args.users

sysPath = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")

console = ConsoleLogger(True)
if __name__ == "__main__":
    ssl_manager = None
    if args.ssl:
        if not args.email:
            parser.error("--email is required when --ssl is enabled (Let's Encrypt requires a contact email).")

        ssl_manager = SSLManager(domain=args.domain, email=args.email, staging=args.staging)

        console.log(f"[SSL] Ensuring certificate for {args.domain} before starting server...")
        ssl_manager.ensure_certificate()

        # Daily 12:00 AM renewal check, with automatic catch-up on
        # startup if a scheduled check was missed (reboot/power loss).
        ssl_manager.start()

    console.log(f"Started server at {HOST}:{PORT} using {THREADCOUNT} threads. "
                f"(HTTPS: {'on, domain=' + args.domain if args.ssl else 'off'})")

    try:
        if args.ssl:
            # waitress has no built-in TLS support, so HTTPS is served
            # with cheroot instead, using the cert/key certbot manages.
            from cheroot.wsgi import Server as WSGIServer
            from cheroot.ssl.builtin import BuiltinSSLAdapter

            server = WSGIServer((HOST, PORT), app, numthreads=THREADCOUNT)
            server.ssl_adapter = BuiltinSSLAdapter(
                certificate=ssl_manager.cert_path, # pyright: ignore[reportOptionalMemberAccess]
                private_key=ssl_manager.key_path, # pyright: ignore[reportOptionalMemberAccess]
            )
            try:
                server.start()
            except KeyboardInterrupt:
                console.log("Shutting down...")
                server.stop()
        else:
            waitress.serve(app, host=HOST, port=PORT, threads=THREADCOUNT)
            # subprocess.Popen([
            #     "mod_wsgi-express", "start-server", "app.py",
            #     "--port", str(PORT),
            #     "--host", HOST,
            #     "--threads", str(THREADCOUNT)
            # ])
    except KeyboardInterrupt:
        console.log("Shutting down...")
    finally:
        if ssl_manager:
            ssl_manager.stop()