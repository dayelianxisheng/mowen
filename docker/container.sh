#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONTAINER_NAME="mowen_sim"

show_help() {
    echo "Usage: $0 [build|start|enter|stop|rebuild]"
    echo "  build   - 构建 Docker 镜像"
    echo "  start   - 启动容器"
    echo "  enter   - 进入容器"
    echo "  stop    - 停止容器"
    echo "  rebuild - 停止旧容器 + 重新构建 + 启动"
}

build_image() {
    echo "Building Docker image..."
    docker compose -f "${SCRIPT_DIR}/docker-compose.yml" build --no-cache
}

start_container() {
    if [ -n "$DISPLAY" ]; then
        xhost +local:docker || true
    fi
    echo "Starting Mowen container..."
    docker compose -f "${SCRIPT_DIR}/docker-compose.yml" up -d
}

enter_container() {
    if ! docker ps | grep -q "$CONTAINER_NAME"; then
        echo "Error: Container is not running. Run '$0 start' first."
        exit 1
    fi
    docker exec -it "$CONTAINER_NAME" bash
}

stop_container() {
    # 先杀 ROS/Gazebo 进程（端口可能被僵尸进程占用）
    "${SCRIPT_DIR}/kill_ros.sh"
    if ! docker ps | grep -q "$CONTAINER_NAME"; then
        echo "Container is not running."
        exit 1
    fi
    docker compose -f "${SCRIPT_DIR}/docker-compose.yml" down
}

rebuild_container() {
    "${SCRIPT_DIR}/kill_ros.sh"
    stop_container
    build_image
    start_container
}

case "$1" in
    help)    show_help ;;
    build)   build_image ;;
    start)   start_container ;;
    enter)   enter_container ;;
    stop)    stop_container ;;
    rebuild) rebuild_container ;;
    *)       show_help ;;
esac