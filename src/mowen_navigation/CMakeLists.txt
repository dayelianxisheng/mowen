cmake_minimum_required(VERSION 3.5)
project(mowen_navigation)

find_package(ament_cmake REQUIRED)

install(DIRECTORY config launch map
  DESTINATION share/${PROJECT_NAME})

ament_package()
