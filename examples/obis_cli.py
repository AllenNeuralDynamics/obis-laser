#!/usr/bin/env python3
"""Connect to an Obis LS laser and enable/disable it at a set power level."""


from obis_laser import ObisLS
import argparse


if __name__ == "__main__":
    parser  = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--enable', action='store_true',
        help="Enable the vibratome head output")
    group.add_argument('--disable', action='store_true',
        help="Disable the vibratome head output")
    parser.add_argument('--wait', type=bool, default=True, required=False,
        help="Wait for the laser to finish warm booting before exiting.")
    parser.add_argument('--port', type=str, default='/dev/ttyACM0',
        help="port name. Leave blank for default.")

    args = parser.parse_args()

    print("Connecting to Obis Laser... ", end=" ", flush=True)
    my_obis = ObisLS(args.port)
    print("done.")

    if args.enable:
        print("Enabling laser output.")
        if args.wait:
            print("  Waiting for warm-boot to complete.")
            my_obis.wait_until_ready()
        my_obis.enable()
    elif args.disable:
        print("Disabling laser output.")
        if args.wait:
            print("  Waiting for warm-boot to complete.")
            my_obis.wait_until_ready()
        my_obis.disable()

