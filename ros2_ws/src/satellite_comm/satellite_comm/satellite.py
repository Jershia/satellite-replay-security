import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class Satellite(Node):
    def __init__(self):
        super().__init__('satellite')

        self.subscription = self.create_subscription(
            String,
            '/telecommand',
            self.receive_command,
            10
        )

    def receive_command(self, msg):
        try:
            data = json.loads(msg.data)

            required_fields = {'command', 'timestamp', 'nonce', 'mac'}

            if required_fields.issubset(data.keys()):
                self.get_logger().info(
                    f"ACCEPTED: command={data['command']}"
                )
            else:
                self.get_logger().info("REJECTED: invalid message")

        except json.JSONDecodeError:
            self.get_logger().info("REJECTED: invalid JSON")


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
