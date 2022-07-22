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
- https://www.oreilly.com/library/view/managing-mission/9781789135077/804a3238-5acc-479d-b593-70567cffede3.xhtml
"""

# DNS blacklist - should contain most of the domains used in the paper
# Domains are from multiple filter lists(from filterlist.com) - geared towards IoT and mobile systems
with open("Blacklist.txt","r") as FilterListFile:
    FilterListTemp = [i.strip() for i in FilterListFile.readlines()]

FilterList = set([])
# Clear comments and blank lines from filter list
for Line in FilterListTemp:
    if len(Line) == 0 or Line[0] == "#":
        continue
    else:
        FilterList.add(Line)

print("Loaded in Filterlist(Blacklist.txt) - please reload software to apply changes you made to this file.")
print("Total domains being blocked: {}".format(len(FilterList)))

# Address and Port proxy software listens on
IPAddress = "127.0.0.1"
Port = 8080

# Address and port of the main/destination DNS server that gets queries forwarded to it
DNSIPAddress = "9.9.9.9"
DNSPort = 9953

ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ServerSocket.bind((IPAddress, Port))
print("DNS Proxy Ready...")
while True:
    try:
        # Recieve Data From User - Blocking
        Data, ClientAddressAndPort = ServerSocket.recvfrom(8192)
        DNSData = dnslib.DNSRecord.parse(Data)


        # Parse DNS Question/Query Data From User and Note Requested Domain
        LabelSet = DNSData.questions[0]._qname.label
        Label = ".".join([i.decode('UTF-8') for i in LabelSet])
        print("Domain Request For: ", Label)
        
        

        if Label in FilterList:# Blacklist

            # If part of blacklist -> send NXDOMAIN reply
            Response = DNSData.reply()
            Response.header.rcode = getattr(dnslib.RCODE,'NXDOMAIN')
            ServerSocket.sendto(Response.pack(),ClientAddressAndPort)
            
            print("Domain Blacklisted By Admin")
        else: # Give to main DNS server
            try:
                # Pass to main DNS server -> send recieved DNS response back to client
                Response = DNSData.send(DNSIPAddress,DNSPort,timeout=5)

                # Check TXID as suggested by DNSlib documentation
                if dnslib.DNSRecord.parse(Response).header.id != DNSData.header.id:
                    raise DNSError('Response transaction id does not match query transaction id. DNS cache poisoning possible.')


                # Send response back to client
                ServerSocket.sendto(Response,ClientAddressAndPort)

                print("Forwarded and Recieved Response For Client")
            except socket.timeout:
                # If timeout -> send NXDOMAIN reply
                Response = DNSData.reply()
                Response.header.rcode = getattr(dnslib.RCODE,'NXDOMAIN')
                ServerSocket.sendto(Response.pack(),ClientAddressAndPort)
                print("Forwarded and Failed To Recieved Response Within Acceptable Time For Client")

        print("*"*20) # Add seperators between requests

    # On Ctrl + C -> unbind socket and close program
    except KeyboardInterrupt:
        print("\nClosing Server...")
        ServerSocket.close()
        sys.exit()
