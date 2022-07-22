import dnslib
import socket
import sys
"""
Resources used:
- https://networkinterview.com/when-does-dns-use-tcp-or-udp/
- https://github.com/paulc/dnslib
- https://stackoverflow.com/questions/24426451/how-to-terminate-loop-gracefully-when-ctrlc-was-pressed-in-python
- https://tutorialedge.net/python/udp-client-server-python/
- https://stackabuse.com/convert-bytes-to-string-in-python/
- https://stackoverflow.com/questions/2675028/list-attributes-of-an-object
- proxy.py from dnslib library
"""
IPAddress = "127.0.0.1"
Port = 8080

DNSIPAddress = "9.9.9.9"
DNSPort = 9953

ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ServerSocket.bind((IPAddress, Port))
print("DNS Proxy Ready...")
while True:
    try:
        Data, ClientAddressAndPort = ServerSocket.recvfrom(8192)
        DNSData = dnslib.DNSRecord.parse(Data)


        LabelSet = DNSData.questions[0]._qname.label
        Label = ".".join([i.decode('UTF-8') for i in LabelSet])
        print("Domain Request For: ", Label)
        
        Response = None # Initialize Response

        if Label == "example.com":# Blacklist example
            Response = DNSData.reply()
            Response.header.rcode = getattr(dnslib.RCODE,'NXDOMAIN')
            ServerSocket.sendto(Response.pack(),ClientAddressAndPort)
        else:
            try:
                Response = DNSData.send(DNSIPAddress,DNSPort,timeout=5)
                ServerSocket.sendto(Response,ClientAddressAndPort)
            except socket.timeout:
                Response = DNSData.reply()
                Response.header.rcode = getattr(dnslib.RCODE,'NXDOMAIN')
                ServerSocket.sendto(Response.pack(),ClientAddressAndPort)

        

        """
        - Make sure to use DNSSEC + check for txid (implement all security DNS measures)
        """

    except KeyboardInterrupt:
        print("\nClosing Server...")
        ServerSocket.close()
        sys.exit()
