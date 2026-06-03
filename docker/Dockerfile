FROM robotis/turtlebot3:humble-latest
ENV LD_LIBRARY_PATH=/opt/ros/humble/lib:${LD_LIBRARY_PATH}

# 代理设置 (构建时通过 --build-arg 传入，或自动使用宿主机 Clash Verge 代理)
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY=localhost,127.0.0.1,.local
ENV HTTP_PROXY=${HTTP_PROXY} \
    HTTPS_PROXY=${HTTPS_PROXY} \
    NO_PROXY=${NO_PROXY}

# 工作空间目录
ENV MOWEN_WS=/root/mowen_ws
RUN mkdir -p ${MOWEN_WS}/src

# 安装 Gazebo 仿真 + ROS2 依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
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

# 写 bashrc，进入容器自动 source 环境
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc && \
    echo "source /usr/share/gazebo/setup.sh" >> ~/.bashrc && \
    echo "source \${MOWEN_WS}/install/setup.bash" >> ~/.bashrc && \
    echo "export ROS_DOMAIN_ID=30" >> ~/.bashrc && \
    echo "export GAZEBO_MODEL_PATH=\${GAZEBO_MODEL_PATH}:\${MOWEN_WS}/install/mowen_gazebo/share/mowen_gazebo/models:\${MOWEN_WS}/install/mowen_radar_fusion/share/mowen_radar_fusion/models" >> ~/.bashrc && \
    echo 'alias cb="colcon build --symlink-install"' >> ~/.bashrc

WORKDIR ${MOWEN_WS}
CMD ["bash"]