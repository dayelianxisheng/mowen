#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONTAINER_NAME="mowen_sim"

show_help() {
    echo "Usage: $0 [start|enter|stop]"
}

start_container() {
    if [ -n "$DISPLAY" ]; then
        xhost +local:docker || true
    fi
    echo "Starting Mowen container..."
    docker compose -f "${SCRIPT_DIR}/docker-compose.yml" pull
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
    if ! docker ps | grep -q "$CONTAINER_NAME"; then
        echo "Container is not running."
        exit 1
    fi
    docker compose -f "${SCRIPT_DIR}/docker-compose.yml" down
}

case "$1" in
    help)  show_help ;;
    start) start_container ;;
    enter) enter_container ;;
    stop)  stop_container ;;
    *)     show_help ;;
esac