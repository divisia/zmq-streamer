import numpy as np
import cv2 as cv
import base64
import time
import zmq
import IO

TIMEOUT = 1000
def initialize_socket(port="555"):
    global socket
    print("[ZMQ SERVER] Socket initializing...", end="")

    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.setsockopt(zmq.RCVTIMEO, TIMEOUT)
    socket.bind("tcp://*:{}".format(port))

    print("\tOK")


def encode_image(img):
    ret, encimg = cv.imencode(".jpg", img)
    b64 = base64.b64encode(encimg)
    return b64


def null_frame():
    nullimg = np.zeros((480, 640, 3))
    enc_img = encode_image(nullimg)
    return enc_img


def send_frame(img):
    st = time.time()
    while (time.time() - st) < TIMEOUT:
        try:
            request = socket.recv()
            if not request == b"<GET>":
                print("[SYNC FAILURE] Trying to synchronise...", end="")
                if request == b"<ACK>":
                    socket.send(b"<OK>")
                    print("\tFIXED")
                    return None

                elif request == b"<BOOT>":
                    print("FIXING")
                    print("[CONNECTION] Client seems restarted. Resynchronising...")
                    socket.send(b"<BOOT_CONFIRM>")
                    #send_frame(img)
                    return None

                else:
                    print("[BAD REQUEST]", request)

            enc_img = encode_image(img)
            socket.send(enc_img)

            response = socket.recv()
            if not response == b"<ACK>":
                print("[BAD RESPONSE] Trying to fix...", end="")
                if response == b"<BOOT>":
                    socket.send(b"<BOOT_CONFIRM>")
                    print("\tFIXED")
                    return None
                elif response == b"<GET>":
                    print("\tNull sending")
                    socket.send(null_frame())
                    res = socket.recv()
                    if not res == b"<ACK>": print("[FUCK] It's screwed up.")
                    socket.recv(b"<OK>")
                    return None
                else:
                    print("[BAD RESPONSE]", response)
                    return None

            socket.send(b"<OK>")

            return True

        except zmq.error.Again:
            print("[CONNECTION] Connection lost.")

    print("[TIMEOUT] Unable to reach client.")

