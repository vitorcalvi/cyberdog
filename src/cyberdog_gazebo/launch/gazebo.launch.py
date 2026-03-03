#!/usr/bin/env python3
"""
CyberDog Gazebo Simulation Launch File
Launches Gazebo with the CyberDog quadruped robot
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command, FindExecutable
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Declare arguments
    declared_arguments = [
        DeclareLaunchArgument(
            'world',
            default_value='empty.world',
            description='World file to load in Gazebo'
        ),
        DeclareLaunchArgument(
            'paused',
            default_value='false',
            description='Start simulation paused'
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation time'
        ),
        DeclareLaunchArgument(
            'gui',
            default_value='true',
            description='Launch Gazebo GUI'
        ),
        DeclareLaunchArgument(
            'headless',
            default_value='false',
            description='Run headless (no GUI)'
        ),
        DeclareLaunchArgument(
            'robot_name',
            default_value='cyberdog',
            description='Robot name'
        ),
        DeclareLaunchArgument(
            'x', default_value='0.0',
            description='Initial x position'
        ),
        DeclareLaunchArgument(
            'y', default_value='0.0',
            description='Initial y position'
        ),
        DeclareLaunchArgument(
            'z', default_value='0.5',
            description='Initial z position'
        ),
    ]

    # Get package paths
    pkg_gazebo = FindPackageShare('cyberdog_gazebo')
    pkg_description = FindPackageShare('cyberdog_description')

    # World file path
    world_file = PathJoinSubstitution([pkg_gazebo, 'worlds', LaunchConfiguration('world')])

    # Get robot description via xacro
    robot_description_content = Command([
        FindExecutable(name='xacro'), ' ',
        PathJoinSubstitution([pkg_description, 'xacro', 'robot.xacro']),
        ' GAZEBO:=true CLASSIC:=false'
    ])

    # Robot state publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description_content,
            'use_sim_time': LaunchConfiguration('use_sim_time'),
        }],
    )

    # Gazebo server (gzserver)
    gzserver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('gazebo_ros'),
                'launch',
                'gzserver.launch.py'
            ])
        ]),
        launch_arguments={
            'world': world_file,
            'paused': LaunchConfiguration('paused'),
            'use_sim_time': LaunchConfiguration('use_sim_time'),
        }.items(),
    )

    # Gazebo client (gzclient)
    gzclient = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('gazebo_ros'),
                'launch',
                'gzclient.launch.py'
            ])
        ]),
        launch_arguments={
            'gui': LaunchConfiguration('gui'),
            'headless': LaunchConfiguration('headless'),
        }.items(),
    )

    # Spawn robot into Gazebo
    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        output='screen',
        arguments=[
            '-entity', LaunchConfiguration('robot_name'),
            '-topic', 'robot_description',
            '-x', LaunchConfiguration('x'),
            '-y', LaunchConfiguration('y'),
            '-z', LaunchConfiguration('z'),
        ],
    )

    return LaunchDescription(
        declared_arguments + [
            robot_state_publisher,
            gzserver,
            gzclient,
            spawn_robot,
        ]
    )
