import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    pkg_share = get_package_share_directory('cyberdog_viz')
    description_share = get_package_share_directory('cyberdog_description')
    
    rviz_config_file = os.path.join(pkg_share, 'rviz', 'cyberdog.rviz')
    
    # Robot State Publisher
    robot_state_publisher_node = Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{
                'robot_description': Command(['xacro', urdf_file]),
                'use_sim_time': LaunchConfiguration('use_sim_time'),
            }],
        )
    
    # Joint State Publisher GUI (optional)
    if LaunchConfiguration('use_jsp_gui'):
        jsg_gui = Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            name='joint_state_publisher_gui',
            output='screen',
            parameters=[{
                'robot_description': Command(['xacro', urdf_file]),
                'use_sim_time': LaunchConfiguration('use_sim_time'),
            }],
        )
    
    # RViz2
    rviz_node = Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=[['-d', rviz_config_file]],
            parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
        )
    ])
    
    return LaunchDescription()
