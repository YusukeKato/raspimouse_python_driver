# raspimouse_python_driver

Pure Python device driver for Raspberry Pi Mouse.

It accesses the hardware through [lgpio](https://abyz.me.uk/lg/py_lgpio.html) and sysfs PWM instead of a kernel module.

Reference: [rt-net/RaspberryPiMouse](https://github.com/rt-net/RaspberryPiMouse) (the official kernel module driver)

## Requirements

- Raspberry Pi 4 (other models are not supported)
- Ubuntu 24.04

## Installation

```bash
sudo apt install python3-lgpio
export PYTHONPATH=/path/to/raspimouse_python_driver:$PYTHONPATH
```

Hardware settings for `/boot/firmware/config.txt`: see [config/boot_config.txt.sample](config/boot_config.txt.sample).
This driver cannot be used together with the rtmouse kernel module.

## Usage

```python
from raspimouse_python_driver import RaspiMouse

with RaspiMouse() as mouse:
    mouse.motor_power.on()
    mouse.motors.set_frequency(left=400, right=400)
    print(mouse.light_sensors.read())
```

## Use with ROS 2

Place this repository in the `src` directory of your workspace and build it:

```bash
cd ~/ros2_ws
rosdep install --from-paths src -y --ignore-src
colcon build --packages-select raspimouse_python_driver
source install/setup.bash
```

Add the dependency to the `package.xml` of your package:

```xml
<exec_depend>raspimouse_python_driver</exec_depend>
```

Example node:

```python
import rclpy
from rclpy.node import Node

from raspimouse_python_driver import RaspiMouse


class LightSensorNode(Node):

    def __init__(self):
        super().__init__('light_sensor_node')
        self.mouse = RaspiMouse()
        self.mouse.open()
        self.timer = self.create_timer(0.1, self.on_timer)

    def on_timer(self):
        self.get_logger().info(str(self.mouse.light_sensors.read()))

    def destroy_node(self):
        self.mouse.close()
        super().destroy_node()


def main():
    rclpy.init()
    node = LightSensorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
```

## Test

```bash
sudo apt install python3-pytest
python3 -m pytest
```

Set `RASPIMOUSE_HARDWARE_TEST=1` to also run tests on a real robot.

## License

[MIT](LICENSE)
