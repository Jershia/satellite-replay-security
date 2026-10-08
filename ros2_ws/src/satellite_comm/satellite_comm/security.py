import hashlib
import hmac
import secrets


SECRET_KEY = b'idp-demo-secret-key'


def generate_nonce():
    return secrets.token_hex(16)


def create_mac(command, timestamp, nonce):
    message = f'{command}|{timestamp}|{nonce}'.encode()

    return hmac.new(
        SECRET_KEY,
        message,
        hashlib.sha256
    ).hexdigest()


def verify_mac(command, timestamp, nonce, mac):
    expected_mac = create_mac(
        command,
        timestamp,
        nonce
    )

    return hmac.compare_digest(
        expected_mac,
        mac
    )