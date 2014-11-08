import os
import struct

s = struct.Struct("H H I I B B H H H 576s")
    #values = (sourcePort, destPort, seqNum, ackNum, headerLength,
            #  flags, receiveWindow, checksum, urgent, data)
packedData = s.pack(55, 55, 0, 0, 0,
              0, 0, 0, 0, "hello")
print len(packedData)
