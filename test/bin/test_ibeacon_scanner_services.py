import time

from ibeacon_scanner.services import ibeacon_init_scanner, ibeacon_get_beacons_data, \
    ibeacon_set_scanner_settings, ibeacon_stop_scanner

def run_fake_scan_test():
    print("[  TEST ] - Inicializing 'run_fake_scan_test' for iBeacon Scanner")
    ibeacon_init_scanner()
    print("[  TEST ] - Setting fake_scan and run")
    ibeacon_set_scanner_settings(scan_tick=3, fake_scan=True, run_flag=True)
    time.sleep(10)
    print("[  TEST ] - Finalizing running fake scan")
    ibeacon_stop_scanner()
    print("[  TEST ] - Obtaining beacon data from scanner:\n{0}".format(ibeacon_get_beacons_data()))
    print("[  TEST ] - Finalizing test for iBeacon Scanner")


if __name__ == "__main__":
    run_fake_scan_test()