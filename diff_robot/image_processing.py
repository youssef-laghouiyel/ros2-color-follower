
import rclpy
from rclpy.node import Node

import cv2
import numpy as np
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from image_object_position_area.msg import Objectdetected


class imageProcess(Node):
    def __init__(self):
        super().__init__('image_process')

        # Subscribe to camera
        self.image_sub = self.create_subscription(
            Image,
            '/camera_sensor/image_raw',
            self.image_recieved_callback,
            10
        )

        # publish to /imageinfo
        self.image_info_pub = self.create_publisher(
            Objectdetected, 
            '/imageinfo',
            10
        )

        self.bridge = CvBridge()

        # ---------- TUNING (robust defaults for RED) ----------
        # Red wraps around hue boundary -> two ranges:
        # Range A: low red near 0
        self.red1_low  = np.array([0,   120,  80], dtype=np.uint8)
        self.red1_high = np.array([10,  255, 255], dtype=np.uint8)

        # Range B: high red near 179
        self.red2_low  = np.array([170, 120,  80], dtype=np.uint8)
        self.red2_high = np.array([179, 255, 255], dtype=np.uint8)

        # Noise filtering
        self.min_area = 800         # ignore small blobs
        self.kernel_open = np.ones((5, 5), np.uint8)
        self.kernel_close = np.ones((7, 7), np.uint8)

        # Logging throttle (avoid spamming terminal)
        self._frame_count = 0

        self.get_logger().info("✅ image_process started. Detecting RED on /camera_sensor/image_raw")

    def image_recieved_callback(self, msg: Image):





        # 1) ROS Image -> OpenCV BGR
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f'Failed to convert image: {e}')
            return

        self._frame_count += 1
        h, w = frame.shape[:2]

        detected = False
        cx = -1 
        cy = -1
        area = 0.0

        # 2) BGR -> HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 3) Build RED mask (two ranges) + combine
        mask1 = cv2.inRange(hsv, self.red1_low, self.red1_high)
        mask2 = cv2.inRange(hsv, self.red2_low, self.red2_high)
        mask = cv2.bitwise_or(mask1, mask2)

        # 4) Morphological cleaning (robust)
        # Open: remove small noise
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel_open, iterations=1)
        # Close: fill holes inside the object
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self.kernel_close, iterations=2)

        # Optional: slight blur to stabilize contour edges
        mask = cv2.GaussianBlur(mask, (5, 5), 0)

        # 5) Find contours (OpenCV compatibility-safe)
        cnts = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = cnts[0] if len(cnts) == 2 else cnts[1]

        annotated = frame.copy()

        # Draw image center line (useful later for control)
        cv2.line(annotated, (w // 2, 0), (w // 2, h), (255, 255, 255), 2)

        if not contours:
            image_info = Objectdetected()
            image_info.cx = cx
            image_info.cy = cy
            image_info.detected = detected
            image_info.area = area
            self.image_info_pub.publish(image_info)

            # If you want: show debug and return
            cv2.putText(annotated, "RED target: NOT FOUND", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.imshow("camera", annotated)
            # cv2.imshow("mask", mask)  # enable if you want to see mask too
            cv2.waitKey(1)
            return

        # 6) Select the largest contour (most stable)
        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)



        if area < self.min_area:
            image_info = Objectdetected()
            image_info.cx = cx
            image_info.cy = cy
            image_info.detected = False
            image_info.area = area
            self.image_info_pub.publish(image_info)


            cv2.putText(annotated, f"RED target too small (area={int(area)})", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.imshow("camera", annotated)
            # cv2.imshow("mask", mask)
            cv2.waitKey(1)
            return
        
        # 7) Centroid + bounding box
        M = cv2.moments(largest)
        if M["m00"] == 0:

            # send the message
            image_info = Objectdetected()
            image_info.cx = cx
            image_info.cy = cy
            image_info.detected = False
            image_info.area = area
            self.image_info_pub.publish(image_info)
            #


            cv2.putText(annotated, "Moment error (m00=0)", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.imshow("camera", annotated)
            cv2.waitKey(1)
            return

        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])

        detected = True

        x, y, w_box, h_box = cv2.boundingRect(largest)

        # 8) Draw overlays
        cv2.drawContours(annotated, [largest], -1, (0, 255, 0), 2)
        cv2.rectangle(annotated, (x, y), (x + w_box, y + h_box), (255, 0, 0), 2)
        cv2.circle(annotated, (cx, cy), 6, (0, 0, 255), -1)

        err = cx - (w / 2.0)
        cv2.putText(annotated, f"RED area={int(area)} cx={cx} cy={cy} err={err:.1f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # 9) Throttled logging (every 15 frames)
        if (self._frame_count % 15) == 0:
            self.get_logger().info(f"RED detected: area={int(area)} center=({cx},{cy}) err={err:.1f}")

        # 10) Show debug
        cv2.imshow("camera", annotated)

        image_info = Objectdetected()
        image_info.cx = cx
        image_info.cy = cy
        image_info.detected = detected
        image_info.area = area
        self.image_info_pub.publish(image_info)


        # cv2.imshow("mask", mask)  # uncomment for mask debug
        cv2.waitKey(1)


def main():
    rclpy.init()
    node = imageProcess()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()
    cv2.destroyAllWindows()

