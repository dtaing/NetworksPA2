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
import datetime

BUFFSIZE = 1024
MSS = 576
ALPHA = .125
BETA = .25
HEADER_LEN = 20

retransmissionTimer = ""
timeout = 1 # second
logFile = ""
retransCount = ""

def main():
    global retransmissionTimer
    filename, remoteIP, remotePort, ackPortNum, logFilename, windowSize = getArgs()
    print "UDP target IP:", remoteIP
    print "UDP target port:", remotePort

    # Create UDP socket and bind to same port as TCP
    dsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dsock.bind(("", ackPortNum))

    # Create TCP socket and bind to same port as UDP
    tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpsock.bind(("", ackPortNum))
    tcpsock.listen(5)

    # Initialize all header flags to 0
    FIN = 0
    SYN = 0
    RST = 0
    PSH = 0
    ACK = 0
    URG = 0

    # Initialize estimatedRTT and devRTT to be 0
    estimatedRTT = 0
    devRTT = 0

    # Initialize the TCP socket's connection state to false so will connect on first loop
    tcpConnected = False

    filesize = os.stat(filename).st_size
    infile = open(filename, "rb")
    global logFile
    logFile = open(logFilename, "w")
    j = 0
    totalBytes = 0
    global retransCount
    retransCount = 0
    for i in range(0, filesize, MSS):
        dataChunk = infile.read(MSS)
        totalBytes += len(dataChunk)
        seqNum = j
        ackNum = j
        # If this segment is last segment, set FIN to 1
        if (j + 1) * MSS >= filesize:
            FIN = 1
        flags = FIN + (SYN << 1) + (RST << 2) + (PSH << 3) + (ACK << 4) + (URG << 5)

        checksum = calcChecksum(dataChunk)
        segmentToSend = createTCPSegment(ackPortNum, remotePort, seqNum, ackNum, HEADER_LEN, flags, 0, checksum, 0, dataChunk)

        sentTime = transmit(dsock, segmentToSend, remoteIP, remotePort)
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
        estimatedRTT = recalcRTT(sentTime, rcvTime, estimatedRTT, devRTT)

        senderIP = socket.gethostbyname(socket.gethostname())
        writeLog(sentTime, rcvTime, senderIP, ackPortNum, remoteIP, remotePort, seqNum, ackNum, ACK, FIN)

        j += 1

    logFile.write("Estimated RTT:" + str(estimatedRTT) + " seconds")
    infile.close()
    logFile.close()
    retransCount -= j
    print "Delivery completed successfully\nTotal bytes sent = " + str(totalBytes) + \
          "\nSegments sent = " + str(j) + "\nSegments retransmitted = " + str(retransCount) + "\n"


def getArgs():
    # Assign command line args to variables and return
    filename = sys.argv[1]
    remoteIP = sys.argv[2]
    remotePort = int(sys.argv[3])
    ackPortNum = int(sys.argv[4])
    logFilename = sys.argv[5]
    windowSize = int(sys.argv[6])
    return filename, remoteIP, remotePort, ackPortNum, logFilename, windowSize

def transmit(dsock, data, remoteIP, remotePort):
    global retransmissionTimer
    global retransCount
    retransmissionTimer = threading.Timer(timeout, transmit, [dsock, data, remoteIP, remotePort])
    retransmissionTimer.start()
    dsock.sendto(data, (remoteIP, remotePort))
    sentTime = datetime.datetime.today()
    retransCount += 1
    return sentTime

def createTCPSegment(sourcePort, destPort, seqNum, ackNum, headerLength, flags, receiveWindow, checksum, urgent, data):
    dataLen = len(data)
    s = struct.Struct("H H I I B B H h H " + str(dataLen) + "s")
    values = (sourcePort, destPort, seqNum, ackNum, headerLength,
              flags, receiveWindow, checksum, urgent, data)
    packedHeader = s.pack(*values)
    return packedHeader

def recalcRTT(sentTime, rcvTime, estimatedRTT, devRTT):
    global timeout
    sampleRTT = (rcvTime - sentTime).total_seconds()
    estimatedRTT = (1 - ALPHA) * estimatedRTT + (ALPHA * sampleRTT)
    devRTT = (1 - BETA) * devRTT + BETA * math.fabs(sampleRTT - estimatedRTT)
    timeout = estimatedRTT + (4 * devRTT)
    return estimatedRTT

def writeLog(sentTime, rcvTime, senderIP, ackPortNum, remoteIP, remotePort, seqNum, ackNum, ACK, FIN):
    global logFile
    timeSegmentSent = str(sentTime)
    sentPacketLog = "Send Segment:" + timeSegmentSent + ", (" + senderIP + ":" + str(ackPortNum) +\
               "), (" + remoteIP + ":" + str(remotePort) + "), " +\
               str(seqNum) + ", " + str(ackNum) + ", ACK:" +\
               str(ACK) + " FIN:" + str(FIN) + "\n"
    logFile.write(sentPacketLog)
    timeSegmentRcv = str(rcvTime)
    rcvPacketLog = "Received Segment:" + timeSegmentRcv + ", (" + remoteIP + ":" + str(remotePort) +\
               "), (" + senderIP + ":" + str(ackPortNum) + "), " +\
               str(seqNum) + ", " + str(ackNum + 1) + ", ACK:" +\
               str(ACK) + " FIN:1" + "\n"
    logFile.write(rcvPacketLog)

# Code taken from http://codewiki.wikispaces.com/ip_checksum.py.
def calcChecksum(data):  # Form the standard IP-suite checksum
    pos = len(data)
    if (pos & 1):  # If odd...
        pos -= 1
        sum = ord(data[pos])  # Prime the sum with the odd end byte
    else:
        sum = 0

    #Main code: loop to calculate the checksum
    while pos > 0:
        pos -= 2
        sum += (ord(data[pos + 1]) << 8) + ord(data[pos])

    sum = (sum >> 16) + (sum & 0xffff)
    sum += (sum >> 16)

    result = (~ sum) & 0xffff #Keep lower 16 bits
    result = result >> 8 | ((result & 0xff) << 8)  # Swap bytes
    print result
    return result

main()