import asyncio
import logging
import ssl
import sys
from pathlib import Path

import envoy
import msgpack
from seot.agent import config
from seot.agent.sinks.mongodb_sink import MongoDBSink

logger = logging.getLogger(__name__)

CERT_DIR_PATH = Path.home() / ".local/share/seot/cert"
CERT_KEY_PATH = CERT_DIR_PATH / "privkey.pem"
CERT_PATH = CERT_DIR_PATH / "cert.key"

SINKS = {
    "mongodb": MongoDBSink
}

SOURCES = {
}


class DPPServer:
    def __init__(self):
        self.server = None
        # task -> (reader, writer)
        self.clients = {}

        if not _cert_exists():
            _generate_cert()
        _check_cert()

        # Load sinks
        self.sinks = []
        for typ, conf in config.get("sinks").items():
            if typ not in SINKS:
                continue
            self.sinks.append(SINKS[typ](**conf))

        # Load sources
        self.sources = []
        for typ, conf in config.get("sources").items():
            if typ not in SOURCES:
                continue
            self.sources.append(SOURCES[typ](**conf))

    def _get_peer_addr(self, writer):
        """ Get address of peer """
        return writer.get_extra_info("peername")

    def _log_ssl_info(self, writer):
        """ Log debugging info on SSL socket """
        compression = writer.get_extra_info("compression")
        (cipher, version, bits) = writer.get_extra_info("cipher")

        logger.info("Compression algorithm: {0}".format(compression))
        logger.info("Cipher algorithm: {0}, SSL version: {1}, Key length: {2}"
                    .format(cipher, version, bits))

    def _accept_client(self, reader, writer):
        """ Accepts a new client connection and launch a task """
        (host, port) = self._get_peer_addr(writer)
        logger.info("Accepted DPP connection from {0}:{1}".format(host, port))
        self._log_ssl_info(writer)

        task = asyncio.Task(self._handle_client(reader, writer))
        self.clients[task] = (reader, writer)

        def client_done(task):
            logger.info("Client disconnected")
            del self.clients[task]

        task.add_done_callback(client_done)

    async def _handle_client(self, reader, writer):
        unpacker = msgpack.Unpacker()

        """ Handle requests from individual clients """
        while True:
            data = await reader.read()
            # Client is disconnected
            if not data:
                break

            unpacker.feed(data)
            for msg in unpacker:
                logger.info("Received DPP message: {0}".format(msg))
                for sink in self.sinks:
                    await sink.write(msg)

    def start(self, loop):
        """ Start TLS server """

        for sink in self.sinks:
            loop.run_until_complete(sink.prepare())
        for source in self.sources:
            loop.run_until_complete(source.prepare())

        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_ctx.load_cert_chain(str(CERT_PATH), str(CERT_KEY_PATH))

        addr = config.get("dpp.listen_address")
        port = config.get("dpp.listen_port")
        logger.info("Launching DPP server at {0}:{1}".format(addr, port))

        async def _start_server():
            self.server = await asyncio.streams.start_server(
                self._accept_client, addr, port, loop=loop, ssl=ssl_ctx
            )

        asyncio.ensure_future(_start_server())

    def stop(self, loop):
        """ Stop TLS server """
        if self.server is not None:
            self.server.close()
            loop.run_until_complete(self.server.wait_closed())
            self.server = None

        for sink in self.sinks:
            loop.run_until_complete(sink.cleanup())
        for source in self.sources:
            loop.run_until_complete(source.cleanup())


def _cert_exists():
    """ Check if certificate exists """
    if not Path(CERT_PATH).is_file() or not Path(CERT_KEY_PATH).is_file():
        return False

    return True


def _generate_cert():
    """ Generate certificate """
    CERT_DIR_PATH.mkdir(parents=True)

    r = envoy.run("which openssl")
    if r.status_code != 0 or r.std_out.strip() == "":
        logger.error("No openssl found in PATH")
        logger.error("Please make sure openssl is installed")
        sys.exit(1)

    logger.info("Generating self-signed certificate using openssl")
    cmd = "openssl req" \
        + " -new" \
        + " -newkey rsa:2048" \
        + " -days 365" \
        + " -nodes" \
        + " -x509" \
        + " -keyout {0}".format(CERT_KEY_PATH) \
        + " -out {0}".format(CERT_PATH) \
        + " -subj \"/C={0}/ST={1}/L={2}/O={3}/OU={4}/CN={5}\"".format(
            "JP", "Osaka", "Ibaraki", "Osaka Univ", "CMC", "seot.org"
        )
    r = envoy.run(cmd)
    if r.status_code != 0:
        logger.error("Failed to generate self-signed certificate:")
        logger.error(r.std_err)
        sys.exit(1)
    logger.info("Certificate successfully generated")
    logger.info("Certificate path: {0}, private key path: {1}".format(
        CERT_PATH, CERT_KEY_PATH
    ))

    CERT_PATH.chmod(0o600)
    CERT_KEY_PATH.chmod(0o600)


def _check_cert():
    """ Check sanity of certificate """
    logger.info("Checking certificate sanity")
    ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    try:
        ssl_ctx.load_cert_chain(str(CERT_PATH), str(CERT_KEY_PATH))
    except ssl.SSLError:
        logger.error("Certificate is broken")
        sys.exit(1)

    logger.info("Certificate looks ok")
