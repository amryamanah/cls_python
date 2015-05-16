from adda import main_adda
from IPython import embed
from os import system


def print_header():
    print("""
Welcome to the Cattle Livestock Test Module 
Available test mode:
0. Exit
1. Try adda
2. Try camera""")

if __name__ == "__main__":
    
    while True:
        print_header()
        test_mode = int(input("Input test mode :"))
        if test_mode == 0:
            break
        elif test_mode == 1:
            main_adda()
        elif test_mode == 2:
            print("amry")
        else:
            print("Test mode {} unavailable".format(test_mode))

    system("pause")