import hashlib
import hmac
import json
import secrets


# Demonstration key only; not suitable for production.
SECRET_KEY = b'idp-demo-secret-key'


def generate_nonce():
    return secrets.token_hex(16)


def create_mac(command, timestamp, nonce, iss=None):
    if iss is None:
        # Preserve compatibility with existing three-argument callers.
        message = f'{command}|{timestamp}|{nonce}'.encode()
    else:
        # Authenticate the command and complete ISS data.
        payload = {
            'command': command,
            'timestamp': timestamp,
            'nonce': nonce,
            'iss': iss,
        }

        message = json.dumps(
            payload,
            sort_keys=True,
            separators=(',', ':'),
            allow_nan=False,
        ).encode('utf-8')

    return hmac.new(
        SECRET_KEY,
        message,
        hashlib.sha256,
    ).hexdigest()


def verify_mac(command, timestamp, nonce, mac, iss=None):
    if not isinstance(mac, str):
        return False

    try:
        expected_mac = create_mac(
            command, timestamp, nonce, iss
        )
    except (TypeError, ValueError):
        return False

    return hmac.compare_digest(expected_mac, mac)
