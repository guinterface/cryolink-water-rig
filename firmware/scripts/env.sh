# Source from this folder. Reuse the existing RoboStack Jazzy setup, own logs/domain.
export ROS_LOG_DIR="$PWD/logs/ros"
export ROS_DOMAIN_ID=89
source cryolink/fsw/env.sh
export PYTHONPATH="$PWD:<scratch>/cryolink_python:${PYTHONPATH:-}"
export PYTHONDONTWRITEBYTECODE=1
