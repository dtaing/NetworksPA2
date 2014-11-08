# sender.py
# Author: Danny Taing
# UNI: dt2461
#

import socket
import sys
import threading
import struct
import os
import math
import time
import datetime

BUFFSIZE = 1024
MSS = 576
ALPHA = .125
BETA = .25

retransmissionTimer = ""
timeout = 1 # second

def main():
    # Assign command line args to variables
    filename = sys.argv[1]
    remoteIP = sys.argv[2]
    remotePort = int(sys.argv[3])
    ackPortNum = int(sys.argv[4])
    #logFilename = sys.argv[5]
    #windowSize = int(sys.argv[6])



    print "UDP target IP:", remoteIP
    print "UDP target port:", remotePort

    dsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dsock.bind(("", ackPortNum))

    tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpsock.bind(("", ackPortNum))
    tcpsock.listen(5)

    global retransmissionTimer
    tcpConnected = False
    filesize = os.stat(filename).st_size
    infile = open(filename, "rb")

    FIN = 0
    SYN = 0
    RST = 0
    PSH = 0
    ACK = 0
    URG = 0
    estimatedRTT = 0
    devRTT = 0
    j = 0
    for i in range(0, filesize, MSS):
        message = infile.read(MSS)

        seqNum = (j * MSS)
        ackNum = (j * MSS)
        if (j + 1) * MSS >= filesize:
            FIN = 1
        flags = FIN + (SYN << 1) + (RST << 2) + (PSH << 3) + (ACK << 4) + (URG << 5)
        messageToSend = createHeader(ackPortNum, remotePort, seqNum, ackNum, 20, flags, 0, 0, 0, message)
        sentTime = transmit(dsock, messageToSend, remoteIP, remotePort)
        rcvTime = ""

        if not tcpConnected:
            tcpConn, tcpAddr = tcpsock.accept()
            print "Connection address:", tcpAddr
            data = tcpConn.recv(BUFFSIZE)
            rcvTime = datetime.datetime.today()
            print "Received ACK:%s" % data
            tcpConnected = True

            retransmissionTimer.cancel()
        elif tcpConnected:
            data = tcpConn.recv(BUFFSIZE)
            rcvTime = datetime.datetime.today()
            print "Received ACK:%s" % data
            retransmissionTimer.cancel()

        # Recalculate estimated RTT based on sample RTT
        global timeout
        sampleRTT = calcRTT(sentTime, rcvTime).total_seconds()
        estimatedRTT = (1 - ALPHA) * estimatedRTT + (ALPHA * sampleRTT)
        devRTT = (1 - BETA) * devRTT + BETA * math.fabs(sampleRTT - estimatedRTT)
        timeout = estimatedRTT + (4 * devRTT)
        print sampleRTT
        print estimatedRTT
        print devRTT
        print timeout
        j += 1

    infile.close()

def transmit(dsock, message, remoteIP, remotePort):
    global retransmissionTimer
    retransmissionTimer = threading.Timer(timeout, transmit, [dsock, message, remoteIP, remotePort])
    retransmissionTimer.start()

    print "Sending packet"
    dsock.sendto(message, (remoteIP, remotePort))
    sentTime = datetime.datetime.today()
    return sentTime


def createHeader(sourcePort, destPort, seqNum, ackNum, headerLength, flags, receiveWindow, checksum, urgent, data):
    dataLen = len(data)
    s = struct.Struct("H H I I B B H H H " + str(dataLen) + "s")
    values = (sourcePort, destPort, seqNum, ackNum, headerLength,
              flags, receiveWindow, checksum, urgent, data)
    packedHeader = s.pack(*values)
    return packedHeader

def calcRTT(sentTime, rcvTime):
    return rcvTime - sentTime


main()