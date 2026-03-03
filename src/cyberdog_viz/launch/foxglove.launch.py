import os
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    # Foxglove Bridge
    foxglove_bridge_node = Node(
        package='foxglove_bridge',
        executable='foxglove_bridge',
        name='foxglove_bridge',
        output='screen',
    )
    
    return LaunchDescription()
