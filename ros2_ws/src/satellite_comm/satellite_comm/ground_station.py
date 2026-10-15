import json
import math
import time
import urllib.request

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from .security import generate_nonce, create_mac


ISS_API = 'https://api.wheretheiss.at/v1/satellites/25544'


def fetch_iss_position():
    request = urllib.request.Request(
        ISS_API,
        headers={
            'User-Agent': 'IDP-Replay-Prevention-Project/1.0'
        },
    )

    with urllib.request.urlopen(request, timeout=5) as response:
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

        self.publisher = self.create_publisher(
            String, '/telecommand', 10
        )
        self.timer = self.create_timer(
            5.0, self.publish_command
        )

    def publish_command(self):
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
            command, timestamp, nonce, iss
        )

        message = {
            'command': command,
            'timestamp': timestamp,
            'nonce': nonce,
            'iss': iss,
            'mac': mac,
        }

        msg = String()
        msg.data = json.dumps(
            message, sort_keys=True, allow_nan=False
        )

        self.publisher.publish(msg)

        self.get_logger().info(
            'Published authenticated STATUS_CHECK '
            f'with ISS position lat={iss["latitude"]:.4f}, '
            f'lon={iss["longitude"]:.4f}'
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
