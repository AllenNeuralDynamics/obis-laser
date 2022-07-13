# OBIS Driver

A python driver for an OBIS laser

## Connection Overview
![](./docs/pics/vibratome_controller_wiring_diagram.png)

## Python Driver Installation

From this directory, invoke:
````
pip install -e .
````

After installation, all of the examples should work.

### for Linux

#### Install UDEV Rules

Install by either copying `10-obis.rules` over to your `/etc/udev/rules.d` folder or by symlinking it with:
````
sudo ln -s /absolute/path/to/obis/10-vibratome.rules /etc/udev/rules.d/10-vibratome.rules
````

Then reload udev rules with
````
sudo udevadm control --reload-rules
````
