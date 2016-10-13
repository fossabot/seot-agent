import logging
import ssl
import sys
from pathlib import Path

import envoy

logger = logging.getLogger("dpp")
logger.setLevel(logging.INFO)

CERT_KEY_PATH = "cert/privkey.pem"
CERT_PATH = "cert/cert.key"


def cert_exists():
    if not Path(CERT_PATH).is_file():
        return False
    if not Path(CERT_KEY_PATH).is_file():
        return False

    return True


def generate_cert():
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


def check_cert():
    logger.info("Checking certificate sanity")
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    try:
        context.load_cert_chain(CERT_PATH, CERT_KEY_PATH)
    except ssl.SSLError:
        logger.error("Certificate is broken")
        sys.exit(1)

    logger.info("Certificate looks ok")


def init():
    logger.info("Initializing DPP subsystem")

    if not cert_exists():
        generate_cert()

    check_cert()

    logger.info("DPP subsystem successfully initialized")
