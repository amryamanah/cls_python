import addapy
from IPython import embed
from os import system

def print_header():
    print("""
Welcome to the Cattle Livestock Test Module 
Available test mode:
0. Exit
1. Cleaning device
2. Automatic adjustment of distance and light
3. Temp, humidity, and illumination
4. Temp and humidity
5. USB ON/OFF/RESET""")

def main_adda(): 
    pl_const_a = -0.2651
    pl_const_b = -26.519
    pl_const_c = 64.118

    pl_led_const_a = 0.0035
    pl_led_const_b = -0.0076
    pl_led_const_c = 0.431

    nopl_const_a = -1.3757
    nopl_const_b = -25.253
    nopl_const_c = 65.843

    nopl_led_const_a = 0.0068
    nopl_led_const_b = 0.0504
    nopl_led_const_c = 0.631

    temp_const_a = 99.77221
    temp_const_b = -49.28702

    illumi_const_a = 934.6479256
    illumi_const_b = -12.13421

    illumi_const_c = 1234.022163
    illumi_const_d = -217.4830

    hum_const_a = 105.69433
    hum_const_b = 6.2141


    
    
    try:
        board = addapy.Initialize_adda()
        if not board:
            raise("Board not initialize")

        while True:
            print_header()
            test_mode = int(input("Input test mode :"))
            if test_mode == 0:
                break
            elif test_mode == 1:
                addapy.device_cleaning()
            elif test_mode == 2:
                try:
                    while True:
                        pl_distance = addapy.get_distance("pl",pl_const_a,pl_const_b,pl_const_c)
                        addapy.set_led("pl", pl_distance, pl_led_const_a, pl_led_const_b, pl_led_const_c)
        
                        nopl_distance = addapy.get_distance("nopl",nopl_const_a,nopl_const_b,nopl_const_c)
                        addapy.set_led("nopl", nopl_distance, nopl_led_const_a, nopl_led_const_b, nopl_led_const_c)

                        if pl_distance < 0:
                            embed()
                        if nopl_distance < 0:
                            embed()

                        print("pl distance = {} nopl distance = {}".format(pl_distance, nopl_distance))
                except KeyboardInterrupt:
                    addapy.set_led("reset", 0, pl_led_const_a, pl_led_const_b, pl_led_const_c)
                    continue
            elif test_mode == 3:
                try:
                    while True:
                        temp = addapy.get_temperature(temp_const_a, temp_const_b)
                        hum = addapy.get_humidity(hum_const_a, hum_const_b)
                        illumination = addapy.get_illumination(illumi_const_a, illumi_const_b, illumi_const_c, illumi_const_d)
                        print("temp = {} hum = {} illumination = {}".format(temp, hum, illumination))
                except KeyboardInterrupt:
                    continue
            elif test_mode == 4:
                pass
            elif test_mode == 5:
                mode = int(input("Choose USB ON/OFF/RESET (1/2/3): "))
                if mode == 1:
                    addapy.set_usb("on")
                elif mode == 2:
                    addapy.set_usb("off")
                elif mode == 3:
                    addapy.set_usb("reset")
                else:
                    print("You put unsupported usb state")
            else:
                print("Test mode {} unavailable".format(test_mode))

    
        destroy = addapy.Destroy_adda()

        if not destroy:
            raise("Board cant be destroyed")
    except Exception as e:
        print(e)
        embed()

