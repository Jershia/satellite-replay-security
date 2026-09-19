import json
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
            10
        )

        self.used_nonces = set()
        self.time_window_s = 5

    def receive_command(self, msg):
        try:
            data = json.loads(msg.data)

            required_fields = {
                'command',
                'timestamp',
                'nonce',
                'mac'
            }

            if not required_fields.issubset(data.keys()):
                self.get_logger().warning(
                    'REJECTED: missing security fields'
                )
                return

            command = data['command']
            timestamp = data['timestamp']
            nonce = data['nonce']
            mac = data['mac']

            if not verify_mac(
                command,
                timestamp,
                nonce,
                mac
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
                f'ACCEPTED: command={command}'
            )

        except json.JSONDecodeError:
            self.get_logger().warning(
                'REJECTED: invalid JSON'
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