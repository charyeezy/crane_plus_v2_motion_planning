#!/usr/bin/env python
###
# File Created: Wednesday, January 16th 2019, 7:18:59 pm
# Author: Charlene Leong charleneleong84@gmail.com
# Modified By: Charlene Leong
# Last Modified: Wednesday, February 6th 2019, 1:00:38 pm
###

import rospkg
import rospy
import moveit_commander
import moveit_msgs.msg
import shape_msgs
import geometry_msgs.msg


class Scene(object):
    """
    Scene Object
    _wait_for_state_update(box_is_known=False, box_is_attached=False, timeout=4): 
                    Validates if scene has been updated with object
    _clear_scene(): Clears the planning scene
    _add_object( dim, pos, rot, col): Adds object to scene
    _load(scene_file): Reads objects from scene file and adds to planning scene interface
    _load_states(scene_file): Loads corresponding states to scene
    """

    PUBLISHER_DELAY = 0.2

    def __init__(self, scene_file):
        self.robot = moveit_commander.RobotCommander()
        self.planning_frame = self.robot.get_planning_frame()
        self.planning_scene = moveit_commander.PlanningSceneInterface()
        self.RVIZ = rospy.get_param('/launch_base/rviz')
        self.ROS_PKG_PATH = rospkg.RosPack().get_path('crane_plus_control')+'/scripts/scenes/'
        # #Object Publishers, can alsu use PlanningSceneInterface, but this doesn throw any warnings
        # self.object_publisher = rospy.Publisher('/collision_object',
        #         moveit_msgs.msg._CollisionObject.CollisionObject,
        #         queue_size=100)

        # self.attached_object_publisher = rospy.Publisher('/attached_collision_object',
        #         moveit_msgs.msg._AttachedCollisionObject.AttachedCollisionObject,
        #         queue_size=30)
        self.NAME = "box"
        self._load_scene(scene_file)
        self._load_states(scene_file)

    def _wait_for_state_update(self, box_is_known=False, box_is_attached=False, timeout=4):
        start = rospy.get_time()
        seconds = rospy.get_time()
        while (seconds - start < timeout) and not rospy.is_shutdown():
            # Test if the base is in attached objects
            attached_objects = self.planning_scene.get_attached_objects([self.NAME])
            is_attached = len(attached_objects.keys()) > 0

            # Test if the base is in the scene.
            # Note that attaching the base will remove it from known_objects
            is_known = self.NAME in self.planning_scene.get_known_object_names()

            # Test if we are in the expected state
            if (box_is_attached == is_attached) and (box_is_known == is_known):
                return True

            # Sleep so that we give other threads time on the processor
            rospy.sleep(0.01)
            seconds = rospy.get_time()

        # If we exited the while loop without returning then we timed out
        return False

    def _clear_scene(self):
        objects = self.planning_scene.get_known_object_names()
        for x in xrange(len(objects)):
            self.planning_scene.remove_world_object(objects[x])
            if(self.RVIZ == True):
                rospy.sleep(self.PUBLISHER_DELAY)

        return self._wait_for_state_update(box_is_known=False)

    def _add_object(self, dim, pos, rot, col):
        if(self.RVIZ == True):
            rospy.sleep(self.PUBLISHER_DELAY)
        pose = geometry_msgs.msg.PoseStamped()
        pose.header.frame_id = self.planning_frame
        pose.pose.position.x = pos[0]
        pose.pose.position.y = pos[1]
        pose.pose.position.z = pos[2]
        self.planning_scene.add_box(self.NAME, pose, (dim[0], dim[1], dim[2]))

        return self._wait_for_state_update(box_is_known=True)

    def _load_scene(self, scene_file):
        rospy.loginfo('Loading %s scene', scene_file)
        self._clear_scene()
        with open(self.ROS_PKG_PATH +scene_file+'.scene') as f:

            lines = 0   # get lines to know amount of blocks
            for line in f:
                lines += 1
            f.seek(0)   # reset readfile location

            title = f.readline()

            # object data is 7 lines long, count amount of objects
            cnt = (lines-2)/7

            for objs in range(0, cnt):
                self.NAME = f.readline()[2:]   # object name
                number = f.readline()     # object number?
                shape = f.readline()      # object shape

                #****** Parsing dimension ******#
                text = f.readline()
                dim = []
                for _ in range(0, 3):  # 3D dimension
                    loc = text.find(' ')
                    dim.append(float(text[:loc]))
                    text = text[loc+1:]  # Remove used text

                #****** Parsing Location ******#
                text = f.readline()
                pos = []
                for _ in range(0, 3):  # 3D dimension
                    loc = text.find(' ')
                    pos.append(float(text[:loc]))
                    text = text[loc+1:]

                #****** Parsing Rotation ******#
                text = f.readline()
                rot = []
                for _ in range(0, 4):  # 4D dimension
                    loc = text.find(' ')
                    rot.append(float(text[:loc]))
                    text = text[loc+1:]

                #****** Parsing Colour ******#
                text = f.readline()
                col = []
                for _ in range(0, 4):
                    loc = text.find(' ')
                    col.append(float(text[:loc]))
                    text = text[loc+1:]
                # Currently unused, also not needed for adding objects

                self._add_object(dim, pos, rot, col)

                #******* adding the object ********#
                # object_shape = shape_msgs.msg._SolidPrimitive.SolidPrimitive()
                # object_shape.type = object_shape.BOX #extend support for other primitives?
                # object_shape.dimensions = dim

                # object_pose = geometry_msgs.msg._Pose.Pose()
                # object_pose.position.x = pos[0]
                # object_pose.position.y = pos[1]
                # object_pose.position.z = pos[2]

                # object_pose.orientation.x = rot[0]
                # object_pose.orientation.y = rot[1]
                # object_pose.orientation.z = rot[2]
                # object_pose.orientation.w = rot[3]

                # object = moveit_msgs.msg.CollisionObject()
                # object.id = name
                # object.header.frame_id = self.planning_frame
                # object.primitives.append(object_shape)
                # object.primitive_poses.append(object_pose)

                # assert type(object) == moveit_msgs.msg.CollisionObject

                # object.header.stamp = rospy.Time.now()
                # object.operation = object.ADD
                # self.object_publisher.publish(object)
        return self._wait_for_state_update(box_is_known=True)

    def _load_states(self, scene_file):
        with open(self.ROS_PKG_PATH+scene_file+'.states') as f:
            content = f.readlines()
        self.states = [x.strip() for x in content]
