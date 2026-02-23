import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
import xacro

# basic launch file to launch the robot_state_publisher with the core_robot.xacro.urdf file

def generate_launch_description():
    

    # package name and urdf file sub path
    pkg_name = "diff_robot"
    subpath_to_description = "description/core_robot.xacro.urdf"
    # full path of the urdf file

    full_path_to_description = os.path.join(get_package_share_directory(pkg_name) , subpath_to_description) 

    # we need to xacro.urdf > .urdf

    xacro_description_file = xacro.process_file(full_path_to_description).toxml()

    # configure the robot state publisher node
    rspLaunchFile = Node(
        package = 'robot_state_publisher',
        executable= 'robot_state_publisher',
        output = 'screen',
        parameters= [{'robot_description': xacro_description_file}]
    )
    # configure the joint_state_publisher_gui node
    jspgLaunchFile = Node(
        package= 'joint_state_publisher_gui',
        executable= 'joint_state_publisher_gui'
    )


    return LaunchDescription([
        rspLaunchFile,
        jspgLaunchFile
    ])
