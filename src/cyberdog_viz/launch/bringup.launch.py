#!/usr/bin/env python3
"""
CyberDog Full Bringup Launch File
Starts visualization, rosbridge, and optional web interface
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Launch arguments
    declared_arguments = [
        DeclareLaunchArgument(
            "use_rviz",
            default_value="true",
            description="Whether to start RViz2",
        ),
        DeclareLaunchArgument(
            "use_foxglove",
            default_value="true",
            description="Whether to start Foxglove Bridge",
        ),
        DeclareLaunchArgument(
            "use_rosbridge",
            default_value="true",
            description="Whether to start Rosbridge Server",
        ),
        DeclareLaunchArgument(
            "use_sim",
            default_value="false",
            description="Whether running in simulation",
        ),
    ]

    # RViz visualization
    rviz_group = GroupAction(
        condition=IfCondition(LaunchConfiguration("use_rviz")),
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource([
                    PathJoinSubstitution([
                        FindPackageShare("cyberdog_viz"),
                        "launch",
                        "visualize.launch.py",
                    ])
                ]),
                launch_arguments={
                    "use_sim": LaunchConfiguration("use_sim"),
                }.items(),
            ),
        ],
    )

    # Foxglove Bridge
    foxglove_group = GroupAction(
        condition=IfCondition(LaunchConfiguration("use_foxglove")),
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource([
                    PathJoinSubstitution([
                        FindPackageShare("cyberdog_viz"),
                        "launch",
                        "foxglove.launch.py",
                    ])
                ]),
            ),
        ],
    )

    # Rosbridge
    rosbridge_group = GroupAction(
        condition=IfCondition(LaunchConfiguration("use_rosbridge")),
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource([
                    PathJoinSubstitution([
                        FindPackageShare("cyberdog_viz"),
                        "launch",
                        "rosbridge.launch.py",
                    ])
                ]),
            ),
        ],
    )

    return LaunchDescription(
        declared_arguments
        + [
            rviz_group,
            foxglove_group,
            rosbridge_group,
        ]
    )
