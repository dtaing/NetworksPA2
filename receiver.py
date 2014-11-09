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
logFile = ""
HEADER_LEN = 20

def main():
    filename, listeningPort, senderIP, senderPort, logFilename = getArgs()

    dsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dsock.bind(("", listeningPort))

    tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print "Waiting on port:%d" % listeningPort

    tcpConnected = False
    outfile = open(filename, "wb")
    global logFile
    logFile = open(logFilename, "w")
    i = 0
    while 1:
        packedData, udpAddr = dsock.recvfrom(BUFFSIZE)

        sourcePort, destPort, seqNum, ackNum, headerLength, flags, receiveWindow, checksum, urgent, data = unpackData(packedData)
        FIN = flags >> 0
        ACK = flags >> 4
        isSame = checkChecksum(sourcePort, destPort, data, checksum)
        seqCheck = i
        if (seqNum == seqCheck and isSame):
            print "Delivery completed successfully from %d" % udpAddr[1]
            outfile.write(data)
            rcvTime = str(datetime.datetime.time(datetime.datetime.now()))

            if not tcpConnected:
                tcpsock.connect((senderIP, senderPort))
                msg = "ACK"
                tcpsock.sendall(msg)
                tcpConnected = True
            elif tcpConnected:
                msg = "ACK"
                tcpsock.sendall(msg)

            sentTime = str(datetime.datetime.time(datetime.datetime.now()))
            rcvrIP = socket.gethostbyname(socket.gethostname())
            writeLog(sentTime, rcvTime, senderIP, sourcePort, rcvrIP, destPort, seqNum, ackNum, ACK, FIN)

            i += 1
            if (FIN == 1):
                break

    outfile.close()
    logFile.close()

def getArgs():
    # Assign command line args to variables and return
    filename = sys.argv[1]
    listeningPort = int(sys.argv[2])
    senderIP = sys.argv[3]
    senderPort = int(sys.argv[4])
    logFilename = sys.argv[5]
    return filename, listeningPort, senderIP, senderPort, logFilename

def unpackData(packedData):
    dataLen = len(packedData) - HEADER_LEN
    s = struct.Struct("H H I I B B H h H " + str(dataLen) + "s")
    sourcePort, destPort, seqNum, ackNum, headerLength, flags, receiveWindow, checksum, urgent, data = s.unpack(packedData)
    return sourcePort, destPort, seqNum, ackNum, headerLength, flags, receiveWindow, checksum, urgent, data

def writeLog(sentTime, rcvTime, senderIP, senderPort, rcvrIP, rcvrPort, seqNum, ackNum, ACK, FIN):
    global logFile
    rcvPacketLog = "Received Packet:" + rcvTime + ", (" + senderIP + ":" + str(senderPort) +\
               "), (" + rcvrIP + ":" + str(rcvrPort) + "), " +\
               str(seqNum) + ", " + str(ackNum) + ", ACK:" +\
               str(ACK) + " FIN:" + str(FIN) + "\n"
    logFile.write(rcvPacketLog)
    sentPacketLog = "Sent Packet:" + sentTime + ", (" + rcvrIP + ":" + str(rcvrPort) +\
               "), (" + senderIP + ":" + str(senderPort) + "), " +\
               str(seqNum) + ", " + str(ackNum + 1) + ", ACK:" +\
               str(ACK) + " FIN:1" + "\n"
    logFile.write(sentPacketLog)

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
    return result

def checkChecksum(sourcePort, destPort, data, checksum):
    newChecksum = calcChecksum(data)
    return newChecksum == checksum

main()