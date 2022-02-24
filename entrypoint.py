import PPP
import os
from time import sleep
import shutil

def main():
    variables_file = '/config/variables.json'
    if os.getenv('SETUP', "False").lower() in ("yes", "true", "t", "1"): 
        try: 
            os.remove(variables_file)
        except: 
            pass 
        PPP.setupVariables(variables_file)
        return

    sleep_for = int(os.getenv('TIMER', 900))
    print('Waiting {} seconds between runs, per TIMER env var'.format(sleep_for))
    while True: 
        PPP.main(variables_file=variables_file)
        sleep(sleep_for)

if __name__ == "__main__": 
    main()