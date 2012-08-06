'''
This script will configure the database for the initial run. All content
must be coded in JSON value-pair syntax.

The configuration data contains information for the infrastructure. Due to
the fact that the peer is able to listen on multiple ports, host and port
must be provided as a list with equal length (same indexes belong to each
other. The maximum amount of conversations is defined via 'maxconv'
attribute (set 'maxconv' to 0 for infinite conversations). Private key,
certificate (public key) and certificate authority file are identified 
via file path.

All configuration data is stored in the 'gossip_crackertable' database
in a document with '_id' = self.

The service data set a sample service for testing purpose. All announced
services are embodied by an 'services' object while a single service
is an object too, consisting of the protocol used by the service, a 
IP adress or DNS name and port number as well as a timeout in seconds. 
A timeout describes the time span after which a service is considered as
faulty.

All service data is stored in the 'gossip_watchlist' database in a document 
with '_id' = self.

@author: Patrick Rockenschaub
'''

from gossip.utils import CouchDBManager, ssldebug

if __name__ == '__main__':
    configdb = CouchDBManager("localhost", "5984", "gossip_crackertable")
    
    sampleconfig = '{' + \
                        '"host": ["localhost"],' + \
                        '"port": [50000],' + \
                        '"maxconv": 25,' + \
                        '"debug": 0,' + \
                        '"verbose": 1,' + \
                        '"certificates": {' + \
                            '"key": "certificates/localserv.pem",' + \
                            '"certificate": "certificates/localservcert.pem",' + \
                            '"ca": "certificates/astaro-ca.pem"' + \
                        '}' + \
                    '}'
    
    ssldebug(sampleconfig)
    
    configdb.write("self", sampleconfig)
    
    servdb = CouchDBManager("localhost", "5984", "gossip_watchlist")
    
    sampleservice = '{"services":{' + \
                        '"sample_service":{'+\
                            '"google": {' + \
                                '"proto": "HTTP",' + \
                                '"port": 80,' + \
                                '"timeout": 600,' + \
                                '"ipv4": "www.google.at"' + \
                                '}' + \
                        '}' + \
                    '}}'
    
    ssldebug(sampleservice)
    
    servdb.write("self", sampleservice)
    
    ssldebug("Database configuration successfully completed")