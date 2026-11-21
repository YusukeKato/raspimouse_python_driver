# raspimouse_python_driver

Pure Python device driver for Raspberry Pi Mouse.

It accesses the hardware through [lgpio](https://abyz.me.uk/lg/py_lgpio.html) and sysfs PWM instead of a kernel module.

This is an unofficial driver developed by volunteers.

Reference: [rt-net/RaspberryPiMouse](https://github.com/rt-net/RaspberryPiMouse) (the official kernel module driver)

## Requirements

- Raspberry Pi 4 (other models are not supported)
- Ubuntu 24.04

## Setup

Run on the Raspberry Pi, in this repository.

1. Install the dependency.

   ```bash
   sudo apt install python3-lgpio
   ```

2. Make sure `/boot/firmware/config.txt` has these lines (see [config/boot_config.txt.sample](config/boot_config.txt.sample)).

   ```
   dtparam=spi=on
   dtparam=i2c_arm=on
   dtparam=i2c_baudrate=62500
   dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4
   ```

   This driver cannot be used together with the official rtmouse kernel module.
   If it was set up before, comment out its overlay, which keeps `/dev/spidev0.0` from being created, and do not load the module.

   ```bash
   sudo sed -i 's/^dtoverlay=anyspi:spi0-0/#&/' /boot/firmware/config.txt
   ```

3. Allow the motors (hardware PWM) without root.

   ```bash
   sudo cp config/99-raspimouse-pwm.rules /etc/udev/rules.d/
   ```

4. Reboot, then check the setup. It prints a command to fix each problem it finds.

   ```bash
   sudo reboot
   ```

   ```bash
   python3 -m raspimouse_python_driver.tools.cli check
   ```

## Usage

Add this repository to `PYTHONPATH`.

```bash
export PYTHONPATH=/path/to/raspimouse_python_driver:$PYTHONPATH
```

```python
import time

from raspimouse_python_driver import RaspiMouse

with RaspiMouse() as mouse:
    print(mouse.light_sensors.read())
    mouse.motor_power.on()
    for _ in range(20):                       # 2 s forward at 0.15 m/s (about 400 Hz)
        mouse.drive.set_velocity(0.15, 0.0)   # linear [m/s], angular [rad/s]
        time.sleep(0.1)
    mouse.drive.stop()
    time.sleep(0.5)
    print(mouse.drive.odometry())
```

`mouse.drive` stops the robot when no velocity command arrives for 0.5 s, so send commands repeatedly while moving.
Wheel geometry, speed and acceleration limits are in `DriveConfig` (defaults from [rt-net/raspimouse2](https://github.com/rt-net/raspimouse2)).

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

Example node that drives by `cmd_vel` and publishes the odometry:

```python
import math

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node

from raspimouse_python_driver import RaspiMouse


class DriveNode(Node):

    def __init__(self):
        super().__init__('drive_node')
        self.mouse = RaspiMouse()
        self.mouse.open()
        self.mouse.motor_power.on()
        self.create_subscription(Twist, 'cmd_vel', self.on_cmd_vel, 10)
        self.odom_pub = self.create_publisher(Odometry, 'odom', 10)
        self.create_timer(0.05, self.publish_odom)

    def on_cmd_vel(self, msg):
        self.mouse.drive.set_velocity(msg.linear.x, msg.angular.z)

    def publish_odom(self):
        odom = self.mouse.drive.odometry()
        msg = Odometry()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'odom'
        msg.child_frame_id = 'base_footprint'
        msg.pose.pose.position.x = odom.x
        msg.pose.pose.position.y = odom.y
        msg.pose.pose.orientation.z = math.sin(odom.theta / 2)
        msg.pose.pose.orientation.w = math.cos(odom.theta / 2)
        msg.twist.twist.linear.x = odom.linear
        msg.twist.twist.angular.z = odom.angular
        self.odom_pub.publish(msg)

    def destroy_node(self):
        self.mouse.close()   # stops the motors and cuts their power
        super().destroy_node()


def main():
    rclpy.init()
    node = DriveNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
```

## Test

Run in this repository. Install pytest first.

```bash
sudo apt install python3-pytest
```

Unit tests (no hardware needed):

```bash
python3 -m pytest
```

Hardware tests on the robot. LEDs light up and the buzzer sounds; do not touch the switches.

```bash
RASPIMOUSE_HARDWARE_TEST=1 python3 -m pytest -v test/hardware
```

Motor and driving tests. Turn on the motor power switch first and put the robot on the floor; it moves forward, backward and turns.

```bash
RASPIMOUSE_HARDWARE_TEST=1 RASPIMOUSE_MOTOR_TEST=1 python3 -m pytest -v -s test/hardware/test_motor_hw.py test/hardware/test_drive_hw.py
```

Check each device by hand with the command line tool:

```bash
python3 -m raspimouse_python_driver.tools.cli led --duration 3
```

```bash
python3 -m raspimouse_python_driver.tools.cli switch --watch --duration 20
```

```bash
python3 -m raspimouse_python_driver.tools.cli buzzer 262 294 330 349 392 --duration 0.4
```

```bash
python3 -m raspimouse_python_driver.tools.cli sensor --watch --duration 15
```

```bash
python3 -m raspimouse_python_driver.tools.cli motor 400 400 --duration 1
```

```bash
python3 -m raspimouse_python_driver.tools.cli drive 0.15 0 --duration 2
```

```bash
python3 -m raspimouse_python_driver.tools.cli drive 0 3.14 --duration 0.5
```

```bash
python3 -m raspimouse_python_driver.tools.cli counter
```

```bash
python3 -m raspimouse_python_driver.tools.cli battery
```

## License

[MIT](LICENSE)
