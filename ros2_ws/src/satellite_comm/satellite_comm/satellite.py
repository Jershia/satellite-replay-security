import json
import math
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from .security import verify_mac


class Satellite(Node):
    def __init__(self):
        super().__init__('satellite')

        self.subscription = self.create_subscription(
            String,
            '/telecommand',
            self.receive_command,
            10,
        )

        self.used_nonces = set()
        self.time_window_s = 5

    def receive_command(self, msg):
        try:
            data = json.loads(msg.data)

            required_fields = {
                'command', 'timestamp', 'nonce', 'iss', 'mac'
            }

            if not isinstance(data, dict):
                self.get_logger().warning(
                    'REJECTED: message must be a JSON object'
                )
                return

            if not required_fields.issubset(data):
                self.get_logger().warning(
                    'REJECTED: missing required fields'
                )
                return

            command = data['command']
            timestamp = data['timestamp']
            nonce = data['nonce']
            iss = data['iss']
            mac = data['mac']

            if (
                not isinstance(command, str)
                or not command
                or isinstance(timestamp, bool)
                or not isinstance(timestamp, int)
                or not isinstance(nonce, str)
                or not nonce
                or not isinstance(iss, dict)
            ):
                self.get_logger().warning(
                    'REJECTED: invalid field types'
                )
                return

            iss_fields = {
                'name', 'id', 'latitude', 'longitude',
                'altitude', 'velocity', 'timestamp', 'units'
            }

            if not iss_fields.issubset(iss):
                self.get_logger().warning(
                    'REJECTED: incomplete ISS data'
                )
                return

            if (
                iss['name'] != 'iss'
                or isinstance(iss['id'], bool)
                or iss['id'] != 25544
                or iss['units'] != 'kilometers'
                or isinstance(iss['timestamp'], bool)
                or not isinstance(iss['timestamp'], int)
            ):
                self.get_logger().warning(
                    'REJECTED: invalid ISS metadata'
                )
                return

            latitude = iss['latitude']
            longitude = iss['longitude']

            if (
                isinstance(latitude, bool)
                or not isinstance(latitude, (int, float))
                or not math.isfinite(latitude)
                or not -90 <= latitude <= 90
                or isinstance(longitude, bool)
                or not isinstance(longitude, (int, float))
                or not math.isfinite(longitude)
                or not -180 <= longitude <= 180
            ):
                self.get_logger().warning(
                    'REJECTED: invalid ISS coordinates'
                )
                return

            for field in ('altitude', 'velocity'):
                value = iss[field]
                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(value)
                    or value < 0
                ):
                    self.get_logger().warning(
                        f'REJECTED: invalid ISS {field}'
                    )
                    return

            # Verify authenticity before accepting any command.
            if not verify_mac(
                command, timestamp, nonce, mac, iss
            ):
                self.get_logger().warning(
                    'REJECTED: invalid MAC'
                )
                return

            current_time = int(time.time())

            if abs(current_time - timestamp) > self.time_window_s:
                self.get_logger().warning(
                    'REJECTED: timestamp outside allowed window'
                )
                return

            if nonce in self.used_nonces:
                self.get_logger().warning(
                    'REJECTED: replayed nonce'
                )
                return

            self.used_nonces.add(nonce)

            self.get_logger().info(
                f'ACCEPTED: command={command}, '
                f'ISS lat={latitude:.4f}, '
                f'lon={longitude:.4f}, '
                f'position_timestamp={iss["timestamp"]}'
            )

        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            self.get_logger().warning(
                'REJECTED: malformed message'
            )


def main(args=None):
    rclpy.init(args=args)
    node = Satellite()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
