import os
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    pkg_share = get_package_share_directory('cyberdog_viz')
    config_file = os.path.join(pkg_share, 'config', 'rosbridge.yaml')
    
    # Rosbridge WebSocket
    rosbridge_node = Node(
        package='rosbridge_server',
        executable='rosbridge_websocket',
        name='rosbridge_websocket',
        output='screen',
        parameters=[config_file],
    )
    
    # Rosapi
    rosapi_node = Node(
        package='rosapi',
        executable='rosapi_node',
        name='rosapi',
        output='screen',
    )
    
    return LaunchDescription()
