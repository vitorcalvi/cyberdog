#!/bin/bash
# CyberDog GUI Stack Startup Script

set -e
WORKSPACE="/home/ubuntu/workspace/cyberdog"

echo "=== CyberDog GUI Stack ==="
echo "Starting services..."

# Source ROS2
source /opt/ros/galactic/setup.bash
source $WORKSPACE/install/setup.bash

# Start Foxglove Bridge
echo "[1/3] Starting Foxglove Bridge on port 8765..."
ros2 launch foxglove_bridge foxglove_bridge.launch.py &
FOXGLOVE_PID=$!

# Start Rosbridge
echo "[2/3] Starting Rosbridge on port 9090..."
ros2 launch rosbridge_server rosbridge_websocket_launch.xml &
ROSBridge_PID=$!

# Start FlexBE WebUI
echo "[3/3] Starting FlexBE WebUI on port 8080..."
ros2 launch flexbe_webui flexbe_ocs.launch.py &
FLEXBE_PID=$!

echo ""
echo "=== GUI Stack Running ==="
echo "Foxglove Bridge: ws://192.168.20.10:8765"
echo "Rosbridge:       ws://192.168.20.10:9090"
echo "FlexBE WebUI:    http://192.168.20.10:8080"
echo ""
echo "Press Ctrl+C to stop all services..."

# Wait for any process to exit
wait -n

# Kill all background processes on exit
kill $FOXGLOVE_PID $ROSBridge_PID $FLEXBE_PID 2>/dev/null
