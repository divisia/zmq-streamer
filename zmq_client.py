import base64
import time
import sys
import IO

import cv2 as cv
import numpy as np
import zmq


TIMEOUT = 1000
HOST = "localhost"
PORT = "555"

def initialize_socket(host, port="555"):
    global socket
    print("[ZMQ RECEIVER] Socket initializing...", end="")

    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.setsockopt(zmq.RCVTIMEO, TIMEOUT)
    socket.connect("tcp://{0}:{1}".format(host, port))
    print("\tOK")

    socket.send(b"<BOOT>")
    try:
        if socket.recv() == b"<BOOT_CONFIRM>":
            print("[ACK CONFIRM] Confirmed.")
    except:
        print("[ACK CONFIRM] Unable to confirm. Server may be dead.")


def null_frame():
    nullimg = np.zeros((480, 640, 3))
    return nullimg


def decode_image(buffer):
    b64 = base64.b64decode(buffer)
    asnp = np.frombuffer(b64, dtype="uint8")
    img = cv.imdecode(asnp, 1)
    return img


def recv_frame():
    global socket

    try:
        socket.send(b"<GET>")

        enc_img = socket.recv()

        try: img = decode_image(enc_img)
        except: return False, None

        socket.send(b"<ACK>")

        response = socket.recv()
        if not response == b"<OK>":
            print("[BAD RESPONSE]", response)
            return False, None

        return True, img

    except Exception as ex:
        print("[SYNC FAILURE] Looking for fixes...", end="")
        try:
            socket.send(b"<BOOT>")
            if socket.recv() == b"<BOOT_CONFIRM>":
                print("\tSOLVED")
                return True, null_frame()
        except:
            try:
                st = time.time()
                while (time.time() - st) < TIMEOUT // 1000 * 10:
                    socket.recv()
                    print("\tSOLVED")
                    return True, null_frame()
            except:
                print("\tFAIL")
                print("[RESTART] Socket is going to be re-initialized.")
                socket.close()
                initialize_socket(HOST)
                return True, null_frame()



