"""test"""

# pylint: disable=import-error, too-few-public-methods, redefined-outer-name

import pytest
from src import main


@pytest.fixture
def patched_run(monkeypatch):
    """fake"""
    calls = []

    class CP:
        """fake class"""

        def __init__(self, rc=0, out="", err=""):
            self.returncode = rc
            self.stdout = out
            self.stderr = err

    def fake_run(cmd, *_args, **_kwargs):
        calls.append(cmd if isinstance(cmd, str) else str(cmd))

        if "source /opt/ros/jazzy/setup.bash" in calls[-1]:
            return CP(
                0, "ROS_DISTRO=jazzy\nAMENT_PREFIX_PATH=/opt/ros/jazzy\n", ""
            )
        if calls[-1].strip().startswith("xhost +local:root"):
            return CP(0, "non-network local connections being added.\n", "")
        if "ros2 pkg create" in calls[-1]:
            return CP(0, "", "")
        if "colcon build" in calls[-1]:
            return CP(0, "", "")
        return CP(0, "", "")

    monkeypatch.setattr(main.subprocess, "run", fake_run)

    return calls


def test_source_ros_env_ok(patched_run):
    """check ros env"""
    rc, out, _err = main.task_source_ros()
    assert rc == 0
    assert "ROS_DISTRO=jazzy" in (out or "")
    assert any("source /opt/ros/jazzy/setup.bash" in c for c in patched_run)


def test_pkg_create_cmd(patched_run):
    """check pkg create command"""
    rc, _out, _err = main.task_pkg_create_cmd()
    assert rc == 0
    cmd = next((c for c in patched_run if "ros2 pkg create" in c), "")
    assert cmd, "ros2 pkg create 명령이 실행되지 않았습니다."

    assert "ros2 pkg create" in cmd
    assert "--build-type ament_python" in cmd
    assert "--license MIT" in cmd
    assert "--dependencies rclpy std_msgs" in cmd
    # 유지보수자/설명 등도 포함되었는지(학생 스펙에 맞춰 조정)
    assert '--maintainer-name "kcci"' in cmd
    assert (
        '--maintainer-email "kcci@kcci.com"' in cmd
        or '--maintainer-email "none@example.com"' in cmd
    )
    assert "D015 homework ROS2 workspace" in cmd


def test_colcon_build_cmd(patched_run):
    """check colcon build command"""
    rc, _out, _err = main.task_colcon_build_cmd()
    assert rc == 0
    cmd = next((c for c in patched_run if "colcon build" in c), "")
    assert cmd, "colcon build 명령이 실행되지 않았습니다."
    assert "colcon build" in cmd
    assert "--symlink-install" in cmd


def test_xhost_cmd(patched_run):
    """check xhost"""
    rc, _out, _err = main.task_xhost_cmd()
    assert rc == 0
    cmd = next((c for c in patched_run if "xhost" in c), "")
    assert cmd.strip().startswith("xhost +local:root")


def test_docker_run_cmd():
    """check the docker command"""
    cmd = main.task_docker_run_cmd().strip()
    assert cmd.startswith("docker run -it --rm --name humble-gui")
    assert "--network=host" in cmd
    assert "-e DISPLAY=$DISPLAY" in cmd
    assert "-v /tmp/.X11-unix:/tmp/.X11-unix:rw" in cmd
    assert "-e ROS_DOMAIN_ID=" in cmd
    assert "-e RMW_IMPLEMENTATION=rmw_cyclonedds_cpp" in cmd
    assert cmd.endswith("arm64v8/ros:humble bash")
