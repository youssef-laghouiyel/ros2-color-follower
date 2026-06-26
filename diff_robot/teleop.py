#!/usr/bin/env python3


import rclpy
from geometry_msgs.msg import Twist
import sys
import select
import termios
import tty
import os

moveBindings = {
    'i': ( 1,  0),
    ',': (-1,  0),
    'j': ( 0,  1),
    'l': ( 0, -1),
    'u': ( 1,  1),
    'o': ( 1, -1),
    'm': (-1,  1),
    '.': (-1, -1),
    'k': ( 0,  0),
}




speedBindings = {
    'q': (1.1, 1.1),
    'z': (0.9, 0.9),
    'w': (1.1, 1.0),
    'x': (0.9, 1.0),
    'e': (1.0, 1.1),
    'c': (1.0, 0.9),
}

MAX_SPEED = 1.0   # m/s
MAX_TURN  = 2.0   # rad/s
MIN_SPEED = 0.1
MIN_TURN  = 0.1

class RobotTeleop:
    def __init__(self):
        rclpy.init()
        self.node = rclpy.create_node('robot_teleop')
        self.publisher = self.node.create_publisher(Twist, '/cmd_vel', 10)

        self.speed = 0.5
        self.turn  = 1.0

        self.print_help()

    def print_help(self):
        os.system('clear')
        print("="*50)
        print("         Robot Teleop Control")
        print("="*50)
        print("  Moving around:")
        print("     u    i    o")
        print("     j    k    l")
        print("     m    ,    .")
        print("")
        print("  k          : stop")
        print("  q/z        : increase/decrease all speeds 10%")
        print("  w/x        : increase/decrease linear speed 10%")
        print("  e/c        : increase/decrease angular speed 10%")
        print("  h          : show help")
        print("  Ctrl-C     : quit")
        print("="*50)
        print(f"  limits:\tmax speed {MAX_SPEED:.1f}\tmax turn {MAX_TURN:.1f}")
        print("="*50)
        print(f"\rcurrently:\tspeed {self.speed:.2f}\tturn {self.turn:.2f}", end='', flush=True)

    def get_key(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            select.select([sys.stdin], [], [], 0)
            key = sys.stdin.read(1)
            return key
        except:
            return None
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def publish(self, linear, angular):
        twist = Twist()
        twist.linear.x = linear
        twist.angular.z = angular
        self.publisher.publish(twist)

    def run(self):
        while True:
            try:
                key = self.get_key()

                if key is None:
                    continue

                if key in moveBindings:
                    linear  = moveBindings[key][0] * self.speed
                    angular = moveBindings[key][1] * self.turn
                    self.publish(linear, angular)

                elif key in speedBindings:
                    self.speed *= speedBindings[key][0]
                    self.turn  *= speedBindings[key][1]

                    # clamp within limits
                    self.speed = max(MIN_SPEED, min(self.speed, MAX_SPEED))
                    self.turn  = max(MIN_TURN,  min(self.turn,  MAX_TURN))

                    print(f"\rcurrently:\tspeed {self.speed:.2f}\tturn {self.turn:.2f}", end='', flush=True)

                elif key == 'h':
                    self.print_help()

                elif key == '\x03':  # Ctrl-C
                    self.publish(0, 0)
                    print("\nExiting...")
                    break

                else:
                    self.publish(0, 0)

            except KeyboardInterrupt:
                self.publish(0, 0)
                print("\nInterrupted")
                break

def main():
    try:
        teleop = RobotTeleop()
        teleop.run()
    finally:
        rclpy.shutdown()

if __name__ == '__main__':
    main()