cmake_minimum_required(VERSION 3.8)
project(mowen_radar_fusion)

# Find ROS2 packages
find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)

# Generate custom radar messages
set(msg_files
  msg/RadarTarget.msg
  msg/RadarTargetArray.msg
)

rosidl_generate_interfaces(${PROJECT_NAME}
  ${msg_files}
  DEPENDENCIES builtin_interfaces std_msgs geometry_msgs
)

ament_export_dependencies(rosidl_default_runtime)

# Install directories (launch, rviz, config, urdf, models)
install(DIRECTORY
  launch
  rviz
  config
  urdf
  models
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
  mowen_radar_fusion/radar_sim_node.py
  mowen_radar_fusion/radar_camera_projector.py
  mowen_radar_fusion/fusion_visualizer_node.py
  mowen_radar_fusion/radar_detector.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
