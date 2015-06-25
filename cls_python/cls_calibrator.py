# -- coding: utf-8 --

__author__ = 'amryfitra'

import os
import addapy
from IPython import embed
import time
from .config_loader import ClsConfig

def print_header():
    print("""
Welcome to the Cattle Livestock Test Module
Available test mode:
0. Exit
1. Cleaning device
2. Automatic adjustment of distance and light
3. Temp, humidity, and illumination
4. Get distance voltage
5. Set led output (1 - 10 V))
6. USB ON/OFF/RESET
7. Auto adjustment of distance using cls_config.ini value""")

def get_distance(cls_config, type):
    if type == "pl":
        const_a = cls_config.PL.getfloat("distance_const_a")
        const_b = cls_config.PL.getfloat("distance_const_b")
        const_c = cls_config.PL.getfloat("distance_const_c")
    elif type == "nopl":
        const_a = cls_config.NOPL.getfloat("distance_const_a")
        const_b = cls_config.NOPL.getfloat("distance_const_b")
        const_c = cls_config.NOPL.getfloat("distance_const_c")

    return addapy.get_distance(type, const_a, const_b, const_c)

def set_led( cls_config, kind, distance):
    if kind == "pl":
        const_a = cls_config.PL.getfloat("led_const_a")
        const_b = cls_config.PL.getfloat("led_const_b")
        const_c = cls_config.PL.getfloat("led_const_c")
    elif kind == "nopl":
        const_a = cls_config.NOPL.getfloat("led_const_a")
        const_b = cls_config.NOPL.getfloat("led_const_b")
        const_c = cls_config.NOPL.getfloat("led_const_c")
    elif kind == "reset":
        return addapy.set_led(kind, distance, 0, 0, 0)
    return addapy.set_led(kind, distance, const_a, const_b, const_c)


def main_calibrator():

    try:
        cls_config = ClsConfig(os.getcwd())
        board = addapy.Initialize_adda()
        if not board:
            raise("Board not initialize")

        while True:
            print_header()
            test_mode = int(input("Input test mode :"))
            try:
                if test_mode == 0:
                    break
                elif test_mode == 1:
                    addapy.device_cleaning()
                elif test_mode == 2:
                    pl_const_a = float(input("Input pl_const_a :"))
                    pl_const_b = float(input("Input pl_const_b :"))
                    pl_const_c = float(input("Input pl_const_c :"))

                    pl_led_const_a = float(input("Input pl_led_const_a :"))
                    pl_led_const_b = float(input("Input pl_led_const_b :"))
                    pl_led_const_c = float(input("Input pl_led_const_c :"))

                    nopl_const_a = float(input("Input nopl_const_a :"))
                    nopl_const_b = float(input("Input nopl_const_b :"))
                    nopl_const_c = float(input("Input nopl_const_c :"))

                    nopl_led_const_a = float(input("Input nopl_led_const_a :"))
                    nopl_led_const_b = float(input("Input nopl_led_const_b :"))
                    nopl_led_const_c = float(input("Input nopl_led_const_c :"))

                    while True:
                        pl_distance = addapy.get_distance("pl", pl_const_a, pl_const_b, pl_const_c)
                        addapy.set_led("pl", pl_distance, pl_led_const_a, pl_led_const_b, pl_led_const_c)

                        nopl_distance = addapy.get_distance("nopl", nopl_const_a, nopl_const_b, nopl_const_c)
                        addapy.set_led("nopl", nopl_distance, nopl_led_const_a, nopl_led_const_b, nopl_led_const_c)

                        if pl_distance < 0:
                            embed()
                        if nopl_distance < 0:
                            embed()

                        print("pl distance = {} nopl distance = {}".format(pl_distance, nopl_distance))

                elif test_mode == 3:
                    temp_const_a = 0
                    temp_const_b = 99.77221
                    temp_const_c = -49.28702

                    illumi_const_a = 934.6479256
                    illumi_const_b = -12.13421
                    illumi_const_c = 1234.022163
                    illumi_const_d = -217.4830

                    with_temp = True
                    hum_const_a = 0
                    hum_const_b = 105.69433
                    hum_const_c = 6.2141

                    while True:
                        temp = addapy.get_temperature(temp_const_a, temp_const_b, temp_const_c)
                        hum = addapy.get_humidity(with_temp, hum_const_a, hum_const_b, hum_const_c)
                        illumination = addapy.get_illumination(illumi_const_a, illumi_const_b, illumi_const_c, illumi_const_d)
                        print("temp = {} hum = {} illumination = {}".format(temp, hum, illumination))

                elif test_mode == 4:
                    kind = input("distance voltage PL or NOPL: ").lower()
                    while True:
                        dist = addapy.get_distance(kind, 0, 1, 0)
                        print("{} distance meter output voltage = {:.5f} V".format(kind, dist))
                        time.sleep(1)

                elif test_mode == 5:
                    kind = input("distance voltage PL or NOPL: ").lower()
                    while True:
                        led_voltage = float(input("set voltage (ex: 1.00): "))
                        print("set led of {} with {} V".format(kind, led_voltage))
                        addapy.set_led(kind, led_voltage, 0, 1, 0)

                elif test_mode == 6:
                    mode = int(input("Choose USB ON/OFF/RESET (1/2/3): "))
                    if mode == 1:
                        addapy.set_usb("on")
                    elif mode == 2:
                        addapy.set_usb("off")
                    elif mode == 3:
                        addapy.set_usb("reset")
                    else:
                        print("You put unsupported usb state")
                elif test_mode == 7:

                    while True:
                        pl_distance = get_distance(cls_config, "pl")
                        set_led(cls_config, "pl", pl_distance)

                        nopl_distance = get_distance(cls_config, "nopl")
                        set_led(cls_config, "nopl", nopl_distance)

                        if pl_distance < 0:
                            embed()
                        if nopl_distance < 0:
                            embed()

                        print("pl distance = {} nopl distance = {}".format(pl_distance, nopl_distance))
                else:
                    print("Test mode {} unavailable".format(test_mode))
            except KeyboardInterrupt:
                addapy.set_led("reset", 0, 0, 0, 0)
                continue

        destroy = addapy.Destroy_adda()

        if not destroy:
            raise("Board cant be destroyed")
    except Exception as e:
        print(e)
