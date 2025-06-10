A set of scripts that setup a simple airplay service in one host and a script on another host that detects that service, connects to it, and streams packets from it.  This is useful for testing a networks capability to support mDNS service discovery and streaming.

'airserv.py' will setup the service on a host and will announce the service every 5 seconds:

```
client1:~/simple-airplay $ sudo python airserv.py 
[INFO] Advertising as 10.0.3.100:7000

Service: Test AirPlay._airplay._tcp.local. on port 7000
Last announcement: 10:51:23
```

'airclient.py' will listen for available services on another host, list them and allow you to select the service you want to subscribe to:

```
client2:~/simple-airplay $ sudo python airclient.py 
Discovered services:
[0] Test AirPlay._airplay._tcp.local. -> 10.0.3.100:7000
Select service index: 
```

Once you select the service, packets will be streamed from the service to the client and graphically displayed.
