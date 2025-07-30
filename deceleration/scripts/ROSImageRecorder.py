import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import time
import os
import argparse
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
import signal
import sys

# Simple tool to record images published by a given ROS2 topic as a video
# @author: Duong Dinh Tran
# @date: 2025/05/21

def parse_args():
    parser = argparse.ArgumentParser(description='Record images from a ROS2 topic and save as video')
    parser.add_argument('-t', '--topic', 
                      default='/sensing/camera/traffic_light/image_raw',
                      help='ROS2 topic name to subscribe to (default: /sensing/camera/traffic_light/image_raw)')
    parser.add_argument('-f', '--fps', 
                      type=int,
                      default=8,
                      help='Frame rate for the output video (default: 8)')
    parser.add_argument('-o', '--output', 
                      help='Output video filename (default: auto-generated with timestamp)')
    return parser.parse_args()

class ImageRecorder(Node):
    def __init__(self, topic_name, fps, output_filename):
        super().__init__('image_recorder')
        
        # Store parameters
        self.topic_name = topic_name
        self.fps = fps
        self.output_filename = output_filename
        
        # Create QoS profile
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        # Create subscriber with QoS profile
        self.subscription = self.create_subscription(
            Image,
            self.topic_name,
            self.image_callback,
            qos_profile)
        
        self.bridge = CvBridge()
        
        self.frames = []
        self.recording = True
        
        #self.get_logger().info(f'Started recording images from topic: {self.topic_name}')
        #self.get_logger().info(f'Frame rate set to: {self.fps} Hz')
        #self.get_logger().info('Press Ctrl+C to stop and save the video.')
        
    def image_callback(self, msg):
        if not self.recording:
            return
            
        # Convert ROS Image message to OpenCV image
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        self.frames.append(cv_image)

    def save_video(self):
        if not self.frames:
            self.get_logger().error('No frames recorded!')
            return

        # Get image dimensions from the first frame
        height, width = self.frames[0].shape[:2]

        # Always save as TempRec.mp4
        # os.makedirs('/home/nimda/AWSIM-Labs-1.3/Recordings/deceleration/ROSRecordings', exist_ok=True)
        output_path = os.path.join('/home/nimda/AWSIM-Labs-1.3/Recordings/deceleration/ROSRecordings', 'TempRec.mp4')

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, self.fps, (width, height))

        for frame in self.frames:
            out.write(frame)

        out.release()
        self.get_logger().info(f'Video saved to {output_path}')
        self.frames = []




def main(args=None):
    cli_args = parse_args()
    rclpy.init(args=args)

    recorder = ImageRecorder(cli_args.topic, cli_args.fps, cli_args.output)

    # Add signal handlers for SIGINT and SIGTERM
    def handle_shutdown(signum, frame):
        recorder.get_logger().info(f'Received signal {signum}. Saving video before shutdown...')
        recorder.save_video()
        rclpy.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    try:
        rclpy.spin(recorder)
    except KeyboardInterrupt:
        handle_shutdown(signal.SIGINT, None)


if __name__ == '__main__':
    main()
