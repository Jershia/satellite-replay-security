import json
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from .security import generate_nonce, create_mac


class GroundStation(Node):
    def __init__(self):
        super().__init__('ground_station')

        self.publisher = self.create_publisher(String, '/telecommand', 10)
        self.timer = self.create_timer(5.0, self.publish_command)

    def publish_command(self):
        command = 'STATUS_CHECK'
        timestamp = int(time.time())
        nonce = generate_nonce()
        mac = create_mac(command, timestamp, nonce)

        message = {
            'command': command,
            'timestamp': timestamp,
            'nonce': nonce,
            'mac': mac
        }

        msg = String()
        msg.data = json.dumps(message)

        self.publisher.publish(msg)
        self.get_logger().info(f'Published secure command: {msg.data}')


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