#!/usr/bin/env python

"""
Publish human pose TFs by converting PoseStamped messages.

You can run this node with rqt_ez_publisher to get a quick-and-dirty GUI to
add and move a virtual human pose.

You can pass in starting positions (length-three tuples) if desired:

    human_pose_publisher.py --initial_hand_pose 0 1 1
                --initial_shoulder_pose 1 0 2

Author: Felix Duvallet <felix.duvallet@epfl.ch>

"""
import argparse
import sys
import yaml

import rospy
import tf
from geometry_msgs.msg import PoseStamped


class PoseToTFRebroadcaster(object):
    """
    Simple node that listens to PoseStamped messages and rebroadcasts
    corresponding TF frames.
    """

    def __init__(self, config=None):
        if config is None:
            config = {}

        self._publish_rate = config.get('publish_rate', 1)
        assert self._publish_rate > 0, 'Must have positive publishing rate.'

        self._frame_configs = config.get('frames', {})
        self._default_parent_frame = 'world'

        # One TF broadcaster
        self._tf_broadcaster = tf.TransformBroadcaster()

        # All the current pose data. Map from frame_name -> PoseStamped.
        self._pose_data = self._init_subscribers()

    def _init_subscribers(self):
        """
        Starts one subscriber per pose topic, and stores the frame name & parent
        associated with each.

        :return: dict(frame_name -> dict('pose'->pose, 'parent_frame'->frame))
        """
        pose_data = {}

        for (frame_name, frame_info) in self._frame_configs.iteritems():
            topic = frame_info.get('pose_topic')
            parent_frame = frame_info.get(
                'parent_frame', self._default_parent_frame)

            # Parse the initial pose, if given in the config.
            frame_position = frame_info.get('initial_position', None)
            initial_pose = None
            if frame_position:
                frame_position = map(float, frame_position.split())
                initial_pose = self.make_stamped_pose(frame_position)

            # Create a new subscriber callback that receives the frame name when
            # it gets called. That subscriber will store the latest pose.
            _ = rospy.Subscriber(
                topic, PoseStamped, self._pose_callback, frame_name)
            pose_data[frame_name] = {'parent_frame': parent_frame,
                                     'pose': initial_pose}
            rospy.logdebug(('Created TF rebroadcaster for pose topic [{}] '
                            '-> frame [{}] with parent').format(
                topic, frame_name, parent_frame))

        return pose_data

    def _pose_callback(self, data, frame_name):
        # Store the latest PoseStamped message.
        self._pose_data[frame_name]['pose'] = data

    @classmethod
    def pose_to_tf(cls, pose, frame_name, parent_frame):
        """
        Generate a TF from a given pose, frame, and parent.

        """
        assert pose is not None, 'Cannot have None for pose.'
        transform = (
            (pose.pose.position.x, pose.pose.position.y, pose.pose.position.z),
            (pose.pose.orientation.x, pose.pose.orientation.y,
             pose.pose.orientation.z, pose.pose.orientation.w),
            rospy.Time.now(),
            frame_name,
            parent_frame)
        return transform

    def publish_transforms(self):
        """
        Publish all currently-known poses as transforms.
        """

        for (frame_name, pose_data) in self._pose_data.iteritems():
            if not pose_data['pose']:
                continue
            transform = self.pose_to_tf(
                pose_data['pose'], frame_name, pose_data['parent_frame'])
            self._tf_broadcaster.sendTransform(*transform)
            rospy.loginfo('Published transform for frame {}.'.format(frame_name))


    @classmethod
    def make_stamped_pose(cls, position):
        """
        Parse a list of positions (that could be None or empty) into a
        PoseStamped ROS message.

        :return A PoseStamped with the identity orientation, or None if the
        input is None or if the list length is not 3.
        """
        initial_pose = None
        if position and len(position) == 3:
            initial_pose = PoseStamped()
            initial_pose.pose.position.x = position[0]
            initial_pose.pose.position.y = position[1]
            initial_pose.pose.position.z = position[2]
            initial_pose.pose.orientation.w = 1.0  # Initialize quaternion properly.
            initial_pose.header.stamp = rospy.Time.now()
        return initial_pose

    def spin(self):
        """
        Publish transforms at the requested rate.
        """
        r = rospy.Rate(self._publish_rate)
        while not rospy.is_shutdown():
            self.publish_transforms()
            r.sleep()


def load_config(config_file):
    config = {}
    with open(config_file, 'r') as f:
        config = yaml.load(f)

    return config


def run(argv):
    rospy.init_node('pose_to_tf_rebroadcaster', anonymous=True)

    # Parse initial pose: can be None or list of elements.
    parser = argparse.ArgumentParser(
        description='Simple Pose->TF rebroadcaster.')
    parser.add_argument('--config_file', required=True,
                        help='YAML configuration file',
                        )

    # Parse arguments and convert into StampedPose.
    args = parser.parse_args(rospy.myargv(argv))
    config = load_config(args.config_file)
    print 'Have configuration: {}'.format(config)

    transform_rebroadcaster = PoseToTFRebroadcaster(config)
    rospy.loginfo('Pose to TF rebroadcaster is now running...')

    transform_rebroadcaster.spin()
    rospy.loginfo('Pose to TF rebroadcaster has finished.')

if __name__ == '__main__':
    arguments = sys.argv[1:]  # argv[0] is the program name.
    run(arguments)