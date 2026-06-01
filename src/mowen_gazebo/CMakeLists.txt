cmake_minimum_required(VERSION 3.0.2)
project(mowen_gazebo)

find_package(catkin REQUIRED)

catkin_package()

install(DIRECTORY launch models rviz urdf worlds
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
