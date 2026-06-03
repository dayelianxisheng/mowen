FROM robotis/turtlebot3:humble-latest

# ============================================================
# 1. 换清华镜像 + 安装 Gazebo + ROS2 依赖
# ============================================================
RUN sed -i 's|http://archive.ubuntu.com|http://mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list \
    && sed -i 's|http://security.ubuntu.com|http://mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list \
    && apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-gazebo-ros-pkgs \
    ros-humble-cartographer-ros \
    ros-humble-nav2-bringup \
    ros-humble-cv-bridge \
    ros-humble-tf2-ros \
    ros-humble-tf2-geometry-msgs \
    ros-humble-teleop-twist-keyboard \
    ros-humble-vision-msgs \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# 2. 工作空间 + bashrc
# ============================================================
ENV MOWEN_WS=/root/mowen_ws
RUN mkdir -p ${MOWEN_WS}/src

RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc && \
    echo "source /usr/share/gazebo/setup.sh" >> ~/.bashrc && \
    echo "source \${MOWEN_WS}/install/setup.bash" >> ~/.bashrc && \
    echo "export ROS_DOMAIN_ID=30" >> ~/.bashrc && \
    echo "export GAZEBO_MODEL_PATH=\${GAZEBO_MODEL_PATH}:\${MOWEN_WS}/install/mowen_gazebo/share/mowen_gazebo/models:\${MOWEN_WS}/install/mowen_radar_fusion/share/mowen_radar_fusion/models" >> ~/.bashrc && \
    echo 'alias cb="colcon build --symlink-install"' >> ~/.bashrc

WORKDIR ${MOWEN_WS}
CMD ["bash"]
