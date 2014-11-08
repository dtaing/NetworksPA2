# receiver.py
# Author: Danny Taing
# UNI: dt2461
#

import socket
import sys
import struct
import datetime

BUFFSIZE = 1024
MSS = 576

def main():
    # Assign command line args to variables
    filename = sys.argv[1]
    listeningPort = int(sys.argv[2])
    senderIP = sys.argv[3]
    senderPort = int(sys.argv[4])
    logFilename = sys.argv[5]

    dsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dsock.bind(("", listeningPort))

    tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print "Waiting on port:%d" % listeningPort

    tcpConnected = False
    outfile = open(filename, "wb")
    i = 0
    while 1:
        packedData, udpAddr = dsock.recvfrom(BUFFSIZE)

        sourcePort, destPort, seqNum, ackNum, headerLength, flags, receiveWindow, checksum, urgent, data = unpackData(packedData)
        FIN = flags >> 0
        ACK = flags >> 4

        seqCheck = i * MSS
        if (seqNum == seqCheck):
            print "Delivery completed successfully from %d" % udpAddr[1]
            outfile.write(data)

            log = open(logFilename, "a")
            timeNow = str(datetime.datetime.time(datetime.datetime.now()))
            destIP = socket.gethostbyname(socket.gethostname())
            messageToLog = timeNow + ", (" + senderIP + ":" + str(sourcePort) +\
                           "), (" + destIP + ":" + str(destPort) + "), " +\
                           str(seqNum) + ", " + str(ackNum) + ", ACK:" +\
                           str(ACK) + " FIN:" + str(FIN) + "\n"
            log.write(messageToLog)
            log.close()

            if not tcpConnected:
                tcpsock.connect((senderIP, senderPort))
                msg = "ACK1"
                tcpsock.sendall(msg)
                tcpConnected = True
            elif tcpConnected:
                msg = "ACK2"
                tcpsock.sendall(msg)
            i = i + 1
            if (FIN == 1):
                break

    outfile.close()

def unpackData(packedData):
    dataLen = len(packedData) - 20
    s = struct.Struct("H H I I B B H H H " + str(dataLen) + "s")
    sourcePort, destPort, seqNum, ackNum, headerLength, flags, receiveWindow, checksum, urgent, data = s.unpack(packedData)
    return sourcePort, destPort, seqNum, ackNum, headerLength, flags, receiveWindow, checksum, urgent, data

main()