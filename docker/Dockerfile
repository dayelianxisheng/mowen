FROM robotis/turtlebot3:humble-latest
ENV LD_LIBRARY_PATH=/opt/ros/humble/lib:${LD_LIBRARY_PATH}
# 工作空间目录
ENV MOWEN_WS=/root/mowen_ws
RUN mkdir -p ${MOWEN_WS}/src

# 写 bashrc，进入容器自动 source 环境
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc && \
    echo "source /usr/share/gazebo/setup.sh" >> ~/.bashrc && \
    echo "source \${MOWEN_WS}/install/setup.bash" >> ~/.bashrc && \
    echo "export ROS_DOMAIN_ID=30" >> ~/.bashrc && \
    echo "export GAZEBO_MODEL_PATH=\${GAZEBO_MODEL_PATH}:\${MOWEN_WS}/install/mowen_gazebo/share/mowen_gazebo/models" >> ~/.bashrc && \
    echo 'alias cb="colcon build --symlink-install"' >> ~/.bashrc

WORKDIR ${MOWEN_WS}
CMD ["bash"]