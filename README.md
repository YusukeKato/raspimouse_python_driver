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

Motor test. Turn on the motor power switch first; the robot moves forward, backward and turns.

```bash
RASPIMOUSE_HARDWARE_TEST=1 RASPIMOUSE_MOTOR_TEST=1 python3 -m pytest -v test/hardware/test_motor_hw.py
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
python3 -m raspimouse_python_driver.tools.cli counter
```

```bash
python3 -m raspimouse_python_driver.tools.cli battery
```

## License

[MIT](LICENSE)
