FROM ubuntu:18.04

ENV DEBIAN_FRONTEND=noninteractive

# ============================================================
# 1. 替换为清华 apt 镜像源 + 安装 ROS Melodic
# ============================================================
RUN sed -i 's|http://archive.ubuntu.com|http://mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list \
    && sed -i 's|http://security.ubuntu.com|http://mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list \
    && apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    lsb-release \
    gnupg2 \
    curl \
    && sh -c 'echo "deb http://mirrors.tuna.tsinghua.edu.cn/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list' \
    && apt-key adv --keyserver 'hkp://keyserver.ubuntu.com:80' --recv-key C1CF6E31E6BADE8868B172B4F42ED6FBAB17C654 \
    && apt-get update

# ============================================================
# 2. ROS Melodic Desktop-Full (含 Gazebo 9 + RViz)
# ============================================================
RUN apt-get install -y --no-install-recommends \
    ros-melodic-desktop-full \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# 3. 补充项目所需的 ROS 包
# ============================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-melodic-gazebo-ros-pkgs \
    ros-melodic-gazebo-ros-control \
    ros-melodic-ros-control \
    ros-melodic-ros-controllers \
    ros-melodic-robot-state-publisher \
    ros-melodic-joint-state-publisher \
    ros-melodic-joint-state-publisher-gui \
    ros-melodic-cartographer-ros \
    ros-melodic-cartographer-rviz \
    ros-melodic-navigation \
    ros-melodic-move-base \
    ros-melodic-amcl \
    ros-melodic-map-server \
    ros-melodic-global-planner \
    ros-melodic-dwa-local-planner \
    ros-melodic-teb-local-planner \
    ros-melodic-teleop-twist-keyboard \
    ros-melodic-laser-filters \
    ros-melodic-tf \
    ros-melodic-tf2 \
    ros-melodic-tf2-ros \
    ros-melodic-rviz \
    ros-melodic-rqt-robot-steering \
    ros-melodic-xacro \
    nano \
    vim \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# 4. 工作空间 + bashrc 环境配置
# ============================================================
ENV MOWEN_WS=/root/mowen_ws
RUN mkdir -p ${MOWEN_WS}/src

RUN echo "source /opt/ros/melodic/setup.bash" >> ~/.bashrc && \
    echo "source /usr/share/gazebo/setup.sh" >> ~/.bashrc && \
    echo "source \${MOWEN_WS}/devel/setup.bash" >> ~/.bashrc && \
    echo "export GAZEBO_MODEL_PATH=\${GAZEBO_MODEL_PATH}:\${MOWEN_WS}/src/mowen_gazebo/models" >> ~/.bashrc && \
    echo 'alias cb="cd \${MOWEN_WS} && catkin_make"' >> ~/.bashrc

# Gazebo 9 在 Ubuntu 24.04 宿主机上的兼容性环境变量
ENV LIBGL_ALWAYS_SOFTWARE=1
ENV MESA_GL_VERSION_OVERRIDE=3.3
ENV GAZEBO_AUDIO_MODE=none

WORKDIR ${MOWEN_WS}
CMD ["bash"]
