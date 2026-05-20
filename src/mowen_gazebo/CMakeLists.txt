cmake_minimum_required(VERSION 3.5)
project(mowen_gazebo)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

find_package(ament_cmake REQUIRED)

install(DIRECTORY launch models rviz urdf worlds
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
