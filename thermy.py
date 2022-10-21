from datetime import datetime
import os
import random
import sys
import threading
import usb.core
import usb.util
import usb.backend.libusb1

from dotenv import load_dotenv
from escpos import *
from flask import Flask, request
from pyngrok import ngrok
import PySimpleGUI as sg
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client

load_dotenv()
app = Flask(__name__)

logo_image_file_location = "img/logotext.png"
icon_file_location = "img/print.ico"
qrcontent_file_name = "qrcontent.txt"
log_file_name = "thermylogs.txt"
qrcontent = []
tunnel_url = ""
sms_phone_number = os.environ.get("TWILIO_PHONE_NUMBER")
logs = ""
thermy_window = ""
print_qrc_bool = True

@app.route('/printpass', methods=['GET', 'POST'])
def printpass():
    body = request.values.get('Body', '').lower().split()
    response = ""
    sms_response = ""
    cmd = body[0]
    if cmd == "pp":
        try:
            studentName = body[1].title()
        except IndexError:
            studentName = ""
        try:
            destination = body[2].title()
        except IndexError:
            destination = ""
        try: 
            reason = body[3].title()
        except IndexError:
            reason = ""
        response = "I'll get right on that!"
        thermy_print("sms", studentName, destination, reason)
    if response != "":
        sms_response = MessagingResponse()
        sms_response.message(response)
    return str(sms_response)

def start_ngrok():
    global tunnel_url
    ngrok.set_auth_token(os.environ.get("NGROK_AUTH_TOKEN"))
    tunnel_url = ngrok.connect(5000).public_url
    client = Client()
    client.incoming_phone_numbers.list(
        phone_number=os.environ.get('TWILIO_PHONE_NUMBER'))[0].update(
            sms_url=tunnel_url + '/printpass')

def load_qrcontent():
    global qrcontent
    global thermy_window
    try:
        qr_file = open(qrcontent_file_name, 'r')
        lines = qr_file.readlines()
        txt_data = ""
        for line in lines:
            if line.strip() != "":
                qrcontent.append(line.strip())
                txt_data += line
        thermy_window["-QRC-"].update(txt_data)
    except:
        pass

def save_logs():
    try:
        log_file = open(log_file_name, 'a')
        log_file.write(logs)
        log_file.close()
    except:
        pass

def is_printer(dev):
    if dev.bDeviceClass == 7:
        return True
    for cfg in dev:
        if usb.util.find_descriptor(cfg, bInterfaceClass=7) is not None:
            return True

def find_and_connect():     
    ''' 
    Default Settings for WelQuic Printer
    idVendor = 0x416
    idProduct = 0x5011
    usb_args = None
    timeout = 5
    in_ep = 0x81
    out_ep = 0x3
    '''
    idVendor = 0
    idProduct = 0
    usb_args = None
    timeout = 0
    in_ep = 0
    out_ep = 0
    backend = usb.backend.libusb1.get_backend(find_library=lambda x: "C:\\Windows\\System32\\libusb-1.0.dll")
    for usbprinter in usb.core.find(backend=backend, find_all=True, custom_match = is_printer):
        idVendor = usbprinter.idVendor
        idProduct = usbprinter.idProduct
        for configuration in usbprinter:
                for interface in configuration:
                    for endpoint in interface:
                        if usb.util.endpoint_direction(endpoint.bEndpointAddress) == usb.util.ENDPOINT_IN:
                            in_ep = endpoint.bEndpointAddress
                        else:
                            out_ep = endpoint.bEndpointAddress
    thermy = printer.Usb(idVendor, idProduct, usb_args, timeout, in_ep, out_ep)
    return thermy

def thermy_print(requestType, studentName, studentDest, studentReason):
    global logs
    logs += requestType + " pass "  
    now = datetime.now()
    origin = os.environ.get("STUDENT_ORIGIN")
    dtString = now.strftime("%m/%d/%Y %I:%M %p")
    try:
        thermy = find_and_connect()
        thermy.set(align='center', font='b', bold=True, underline=2, 
            width=2, height=2, density=8, invert=False, smooth=True,
            flip=False, double_width=False, double_height=False,
            custom_size=True)
        thermy.image(logo_image_file_location, high_density_vertical=True, high_density_horizontal=True, impl="bitImageRaster",
                    fragment_height=1024, center=True)
        thermy.textln(dtString)
        logs += dtString + " "
        if studentName != "":
            thermy.textln(studentName)
            logs += studentName
        thermy.textln(" from " + origin)
        if studentDest != "":
            thermy.textln("to " + studentDest)
            logs += " to " + studentDest
        if studentReason != "":
            thermy.textln("for " + studentReason)
            logs += " b/c " + studentReason
        if len(qrcontent) > 0 and print_qrc_bool:
            thermy.qr(random.choice(qrcontent), ec=0, size=6, model=2, native=False, center=True, impl='bitImageRaster')
        thermy.cut()
        thermy.close()
    except:
        logs += "error"
        if requestType == "btn":
            thermy_window["-LOG-"].update(logs)
            raise Exception("PrinterError")
    logs += "\n"
    thermy_window["-LOG-"].update(logs)

if __name__ == '__main__':
    # start ngrok once
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        start_ngrok()
    
    # main window layout
    sg.theme("Darkblue16")
    input_size = (25, 1)

    server_status = "offline"
    if "ngrok" in tunnel_url:
        server_status = "online"

    sglayout_tab_pass = [
                [sg.Image(logo_image_file_location, pad=(10, 10))],
                [sg.Frame("info (optional)", [
                    [sg.Push(), sg.Text("who?"), sg.Input(size=input_size, key="-NAME-")],
                    [sg.Push(), sg.Text("where?"), sg.Input(size=input_size, key="-DEST-")],
                    [sg.Push(), sg.Text("why?"), sg.Input(size=input_size, key="-REASON-")]
                ], pad=(10, 10) )],
                [sg.Frame("actions", [
                    [sg.Button("print"), sg.Checkbox(text="qrc", key="-QR_CHECK-", enable_events=True, default=True), sg.Button("about"), sg.Button("exit")] 
                ], pad=(10, 10) )], 
            ]

    sglayout_tab_server = [  
                [sg.Frame("server status (" + server_status + ")", [
                    [sg.Text("webhook tunnel url:")],
                    [sg.StatusBar(tunnel_url, font="Courier 10", key="-URL-")],
                    [sg.Text("sms phone number:")],
                    [sg.StatusBar(sms_phone_number, font="Courier 10", key="-SMS-")]
                ], pad=(10, 10) )]
            ]

    sglayout_tab_logs = [  
                #[sg.Button("refresh", pad=(5, 5))],
                [sg.Multiline("", font="Courier 12", key="-LOG-", size=(60, 20), write_only=True, expand_y=True,
                                auto_refresh=True, horizontal_scroll=True, disabled=True)],
            ]
            
    sglayout_tab_qrc = [  
                [sg.Multiline("", font="Courier 12", key="-QRC-", size=(60, 20), write_only=True, expand_y=True,
                                auto_refresh=True, horizontal_scroll=False, disabled=True)],
            ]
    
    sglayout = [[sg.TabGroup([[ sg.Tab('pass', sglayout_tab_pass, element_justification="center"),
                                sg.Tab('qrc', sglayout_tab_qrc, element_justification="center"),
                                sg.Tab('server+sms', sglayout_tab_server, element_justification="center"), 
                                sg.Tab('logs', sglayout_tab_logs, element_justification="center")
                            ]])
                ]]
         
    thermy_window = sg.Window(title="thermy v0.2", 
                            layout=sglayout,
                            icon=icon_file_location,
                            element_justification="center",
                            element_padding=(5, 5),
                            margins=(5, 5),
                            font="Courier 14",
                            enable_close_attempted_event=True,
                            grab_anywhere=True,
                            finalize=True
    )

    # load qrcodes from txt file
    load_qrcontent() 

    # start flask as deamon thread
    flask_thread = threading.Thread(target=lambda: app.run(debug=False, use_reloader=False))
    flask_thread.setDaemon(True)
    flask_thread.start()

    # note: correct startup order above is: 1) ngrok; 2) window setup; 3) load qrcontent; 4) flask.

    # main window loop
    while True:
        event, values = thermy_window.read()
        if (event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT or event == 'exit') and sg.popup_yes_no('Do you really want to exit?', font="Courier 10", grab_anywhere=True) == 'Yes':
            break
        elif event is None:
            continue
        elif event == "-QR_CHECK-":
            print_qrc_bool = not print_qrc_bool
        elif event == "print":
            thermy_window["print"].disabled = True
            studentName = values['-NAME-']
            studentDest = values['-DEST-']
            studentReason = values['-REASON-']
            try:
                thermy_print("btn", studentName, studentDest, studentReason)
            except:
                sg.popup("Oops!  Something didn't quite work.",  
                            "Make sure your USB thermal printer is connected.  Then, try again.",  
                            "If that doesn't work, restart the program and your thermal printer.", 
                            "Notes:",
                            "--Libusbk driver required (available in Zadig Automated Driver Installer).",
                            font="Courier 12", non_blocking=True, grab_anywhere=True)
            thermy_window["print"].disabled = False
        #elif event == "refresh":
        #    thermy_window["-LOG-"].update(logs)
        elif event == "about":
            sg.popup('about thermy', 'simple thermal printing', 'version 0.2', 'MIT license',  font="Courier 12", non_blocking=True, grab_anywhere=True)    
    
    # cleanup and exit
    thermy_window.close()
    save_logs()
    ngrok.disconnect(tunnel_url)
    ngrok.kill()
    sys.exit(0)
    