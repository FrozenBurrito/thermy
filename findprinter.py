import usb.core 
import usb.util
import usb.backend.libusb1

def is_printer(dev):
    if dev.bDeviceClass == 7:
        return True
    for cfg in dev:
        if usb.util.find_descriptor(cfg, bInterfaceClass=7) is not None:
            return True

backend = usb.backend.libusb1.get_backend(find_library=lambda x: "C:\\Windows\\System32\\libusb-1.0.dll")
for printer in usb.core.find(backend=backend, find_all=True, custom_match = is_printer):
    print(printer)
    for configuration in printer:
            for interface in configuration:
                for endpoint in interface:
                    print(endpoint.bEndpointAddress)
                    if usb.util.endpoint_direction(endpoint.bEndpointAddress) == usb.util.ENDPOINT_IN:
                        print("IN")
                    else:
                        print("OUT")
                    
