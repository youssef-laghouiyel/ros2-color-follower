import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from image_object_position_area.msg import Objectdetected
import cv2

class controlNode(Node):
    def __init__(self):
        super().__init__('control_node')
        # let's create a subscription to /imageinfo
        self.sub = self.create_subscription(
            Objectdetected , 
            '/imageinfo',
            self.poisition_area_callback,
            10
        )
        # create a publisher to the /cmd_vel topic
        self.pub = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )
        # some parameters
        self.target_area = 20000.0
        self.image_center_x = 640/2
        self.K_ang = 0.0025
        self.K_lin = 0.0002 

        # search parameters
        self.search_turn = 0.35         # rad/s
        self.search_step_lin = 0.05     # m/s
        self.search_step_period = 2     # every 2s
        self.search_step_duration = 0.5 # step Lasts
        self.search_timeout = 12        # after 12s stop
        self.last_seen_time = self.get_clock().now()
        self.last_search_step_time = self.get_clock().now()
        # control the loop timer
        self.LatestObj = None
        self.timer_cmd = self.create_timer(0.05 , self.cmd_timer_callback) # 20 hz


    def poisition_area_callback(self , msg:Objectdetected):

        self.LatestObj = msg
        if msg.detected :
            self.last_seen_time = self.get_clock().now()

            




    def cmd_timer_callback(self):
        cmd = Twist()

        # get current time
        now = self.get_clock().now()
        # search if object dissapeared for 12 sec

        if (self.LatestObj is None) or ( not self.LatestObj.detected):
            stopTime = (now - self.last_seen_time).nanoseconds * 1e-9
            # search if the stop time exceeds the search time out
            if stopTime > self.search_timeout :
                # if so stop the robot 
                cmd.linear.x = 0.0
                cmd.angular.z = 0.0
                return
            
            # Rotate a little bite
            cmd.angular.z = self.search_turn
            # small steps forward sometimes
            dt_step = (now - self.last_search_step_time).nanoseconds * 1e-9
            phase = dt_step % self.search_step_period


            if phase < self.search_step_duration:
                cmd.linear.x = self.search_step_lin
            else:
                cmd.linear.x = 0.0

            self.pub.publish(cmd)
            return
        
        # Follow mode
        cx = float(self.LatestObj.cx)
        area = float(self.LatestObj.area)
        error_x = cx - self.image_center_x
        error_area = self.target_area - area
        
        cmd.angular.z = -self.K_ang * error_x
        cmd.linear.x = self.K_lin * error_area

        # clamps for safety

        if cmd.linear.x > 0.25 : cmd.linear.x = 0.25
        if cmd.linear.x < -10  : cmd.linear.x = -0.10


        if cmd.angular.z > 1.0 : cmd.angular.z = 1.0
        if cmd.angular.z < -1.0: cmd.angular.z = -1.0

        # send the command
        self.pub.publish(cmd)



        
def main():
    rclpy.init()
    node = controlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()
    cv2.destroyAllWindows()


        


        

    
