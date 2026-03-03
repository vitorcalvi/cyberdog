# CyberDog Unified Repository

A unified ROS2 repository for Xiaomi CyberDog robot, combining hardware and simulation packages.

## Overview

This repository merges the original `cyberdog_ros2` packages with new simulation capabilities, providing a complete development environment for the CyberDog robot.

## Packages

### Hardware Packages (from cyberdog_ros2)
- **cyberdog_bringup** - Launch files and hardware bringup
- **cyberdog_ception** - Perception (BMS, body state, sensors, detection)
- **cyberdog_common** - Common utilities, gRPC, vendors
- **cyberdog_decision** - Decision making and autonomy
- **cyberdog_interaction** - Human-robot interaction
- **cyberdog_interfaces** - ROS2 message/service definitions
- **cyberdog_motion** - Motion control
- **tools** - Documentation and utilities

### Simulation Packages (NEW)
- **cyberdog_description** - URDF, xacro, and meshes for Gazebo
- **cyberdog_gazebo** - Gazebo Classic simulation
- **cyberdog_locomotion** - Locomotion control framework

## Requirements

- ROS2 Galactic (Ubuntu 18.04 / Jetson)
- Docker (recommended for development)

## Quick Start

### Using Docker (Recommended)

```bash
# Build the Docker image
docker compose build

# Start the development container
docker compose up -d

# Enter the container
docker compose exec cyberdog-dev bash

# Build the workspace
source /opt/ros/galactic/setup.bash
colcon build --symlink-install
```

### Build from Source

```bash
mkdir -p ~/cyberdog_ws/src
cd ~/cyberdog_ws/src
git clone https://github.com/vitorcalvi/cyberdog.git .
cd ..
colcon build --symlink-install
```

## License

Apache 2.0 (from original Xiaomi CyberDog)

## Sources

- Original: https://github.com/MiRoboticsLab/cyberdog_ros2
- Fork: https://github.com/vitorcalvi/cyberdog_ros2
- Description reference: https://github.com/legubiao/quadruped_ros2_control
