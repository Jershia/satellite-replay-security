import json
import math
import time
import urllib.request

import rclpy
from rclpy.node import Node

from .security import generate_nonce, create_mac


ISS_API = 'https://api.wheretheiss.at/v1/satellites/25544'


def fetch_iss_position():
    request = urllib.request.Request(
        ISS_API,
        headers={
            'User-Agent': 'IDP-Replay-Prevention-Project/1.0'
        },
    )

    with urllib.request.urlopen(request, timeout=10) as response:
        data = json.loads(response.read().decode('utf-8'))

    if data.get('name') != 'iss' or data.get('id') != 25544:
        raise ValueError('Unexpected satellite returned by API')

    iss = {
        'name': 'iss',
        'id': 25544,
        'latitude': float(data['latitude']),
        'longitude': float(data['longitude']),
        'altitude': float(data['altitude']),
        'velocity': float(data['velocity']),
        'timestamp': int(data['timestamp']),
        'units': data['units'],
    }

    if not -90 <= iss['latitude'] <= 90:
        raise ValueError('Invalid ISS latitude')

    if not -180 <= iss['longitude'] <= 180:
        raise ValueError('Invalid ISS longitude')

    for field in ('altitude', 'velocity'):
        if not math.isfinite(iss[field]) or iss[field] < 0:
            raise ValueError(f'Invalid ISS {field}')

    if iss['timestamp'] <= 0:
        raise ValueError('Invalid ISS timestamp')

    if iss['units'] != 'kilometers':
        raise ValueError('Unexpected API units')

    return iss


class GroundStation(Node):
    def __init__(self):
        super().__init__('ground_station')

        # Replace with Laptop 2's actual Windows LAN IP.
        self.server_ip = self.declare_parameter(
            'server_ip',
            '10.88.41.92'
        ).value

        self.timer = self.create_timer(
            5.0,
            self.send_command
        )

        self.get_logger().info(
            f'Ground Station sending ISS data to '
            f'http://{self.server_ip}:8000/telecommand'
        )

    def send_command(self):
        try:
            iss = fetch_iss_position()
        except Exception as exc:
            self.get_logger().warning(
                f'ISS fetch failed; command not sent: {exc}'
            )
            return

        command = 'STATUS_CHECK'
        timestamp = int(time.time())
        nonce = generate_nonce()

        mac = create_mac(
            command,
            timestamp,
            nonce,
            iss
        )

        message = {
            'command': command,
            'timestamp': timestamp,
            'nonce': nonce,
            'iss': iss,
            'mac': mac,
        }

        data = json.dumps(
            message,
            sort_keys=True,
            allow_nan=False
        ).encode('utf-8')

        url = f'http://{self.server_ip}:8000/telecommand'

        request = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                result = response.read().decode('utf-8')

                self.get_logger().info(
                    f'ISS lat={iss["latitude"]:.4f}, '
                    f'lon={iss["longitude"]:.4f}; '
                    f'FastAPI response: {result}'
                )

        except Exception as exc:
            self.get_logger().error(
                f'Failed to send telecommand to FastAPI: {exc}'
            )


def main(args=None):
    rclpy.init(args=args)
    node = GroundStation()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
