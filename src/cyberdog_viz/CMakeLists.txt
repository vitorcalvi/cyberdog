cmake_minimum_required(VERSION 3.8)
project(cyberdog_viz)

find_package(ament_cmake REQUIRED)
find_package(rviz_common REQUIRED)
find_package(rviz_rendering REQUIRED)
find_package(rviz_default_plugins REQUIRED)
find_package(robot_state_publisher REQUIRED)
find_package(joint_state_publisher REQUIRED)
find_package(joint_state_publisher_gui REQUIRED)
find_package(xacro REQUIRED)
find_package(foxglove_bridge REQUIRED)
find_package(rosbridge_suite REQUIRED)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  find_package(ament_lint_common REQUIRED)
endif()

install(DIRECTORIES
  rviz launch config worlds
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
