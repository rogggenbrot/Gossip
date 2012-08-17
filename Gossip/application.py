'''
@author: Patrick Rockenschaub
'''

import simplejson
import traceback
import time

from gossip.crackertable import Babblemouth, Conversation
from gossip.stationhouse import Supervisor, HTTPService
from gossip.utils import CouchDBManager, ssldebug
from M2Crypto import X509

babbler = None
checker = None

def startgossip():
    def metahandler( conv, msg ):
    #--------------------------------------------------------------------------
        """
        Handle the connection establishment. 
        
        Each side starts by sending their known babblers encoded as JSON data. Parse this
        data using simplejson and load them one by one by calling 'loadbabbler' method.
        
        After the babblers have been loaded they are stored in the database and a request
        for a update of the service list is sended.
        
        :param conv: conversation instance from which the message has been received
        :param msg: actual message data as string
        """
        
        ssldebug("Synchronizing babblers with %s" % conv.id)
        
        table = simplejson.loads(msg)
        
        for identifier in table:
            babbler.loadbabbler(identifier, table[identifier], conv)
        
        savebabblertodb(babbler)
        
        ssldebug("Synchronizing done with %s" % conv.id)
        
        conv.senddata("SREQ", conv.getmessagesequence(), "Service request")
    #--------------------------------------------------------------------------
    
    def servupdhandler( conv, msg ):
    #--------------------------------------------------------------------------
        """
        Handles a incoming service update.
        
        The incoming service data will be stored in a couchDB document with same 
        name as the babbler identifier.
        
        :param conv: conversation instance from which the message has been received
        :param msg: actual message data as string
        """
        
        if conv.id != babbler.myid:
            servdb.write(conv.id, msg)
            servdb.compact()
    #--------------------------------------------------------------------------  
    
    def servreqhandler( conv, msg ):
    #--------------------------------------------------------------------------
        """
        Handle an incoming service request by replying own service list.
        
        Read the own service list from database and send it back to the
        requester.
        
        :param conv: conversation instance from which the message has been received
        :param msg: actual message data as string
        """
        
        services = servdb.read("self")
        if conv.status == Conversation.GOING_ON:
            conv.senddata("SUPD", conv.getmessagesequence(), services)
    #--------------------------------------------------------------------------   
    
    def loadconfiguration():
    #------------------------------------------------------------------------- 
        """
        Load configuration file in JSON notation specifying debug options, 
        list of host/port which to listen to and paths to certification files.
        
        For example configuration data see 'database_setup.py'.
        
        Anything missing will cause error the ensure a proper configuration 
        in order to be able to work correctly.
        
        :raise Exception: any error will be printed as traceback and raised
                            without further description
        """
        
        try:
            db = CouchDBManager("localhost", "5984", "gossip_crackertable")
            jsondata = db.read("self")
            
            config = simplejson.loads(jsondata)
            
            config["debug"] = int(config["debug"])
            config["verbose"]  = int(config["verbose"])
            config["maxconv"] = int(config["maxconv"])
            
            if not isinstance(config["host"], list) or not isinstance(config["port"], list):
                raise ValueError("Host and port must be provided as a list in the configuration file.")
        
            if not config.has_key("version"):
                config["version"] = 1
        except KeyboardInterrupt:
            raise
        except:
            traceback.print_exc()
            
            raise Exception("Configuration file couldn't be loaded")
        
        return config
    #-------------------------------------------------------------------------    
    
    def loadbabblersfromdb( babbler ):
    #--------------------------------------------------------------------------
        """
        Read saved babbler table from database and load them into 'self.babblers'.
        
        Calls 'babbler.loadbabblers' to process the data received from the disk.
        """
        db = CouchDBManager("localhost", "5984", "gossip_crackertable")
        try:            
            documents = db.getdocumentlist()
            for doc in documents:
                if doc != "self":
                    data = db.read(doc)
                    babbler.loadbabbler(doc, simplejson.loads(data))
        except KeyboardInterrupt:
            raise
        except:
            traceback.print_exc()

    #--------------------------------------------------------------------------
    
    def savebabblertodb( babbler ):
    #--------------------------------------------------------------------------
        """
        Save list of babbler to a file called 'crackerbarrel.json'. Certificates
        are stored separatly in a subfolder of 'certs'.
        
        While babbler data is stored in a central file, each certificate is saved
        separately. File is locked during writing process.
        """
        db = CouchDBManager("localhost", "5984", "gossip_crackertable")
        try:
            for identifier in babbler.babblers:
                db.write(identifier, babbler.getbabbler(identifier).contact.tojson())
                db.compact()
                
                if babbler.getbabbler(identifier).x509 != None:
                    babbler.getbabbler(identifier).x509.save("%s/%s.pem" % (Babblemouth.CERTIFICATE_FOLDER, identifier), X509.FORMAT_PEM)
            
        except KeyboardInterrupt:
            raise
        except:
            print "Unable to save babblers"
            traceback.print_exc()
        
    #--------------------------------------------------------------------------    
    
    def processserviceupdate( document ):
    #--------------------------------------------------------------------------
        """
        Handle a update of own service list.
        
        Will be called by couchDB change notifier if the own service list is altered
        and sends service updates to all known babblers.
        
        :param document: document which has been altered (passed by CouchDBHandler.watchdbthreading).
        """
        
        try:            
            babbler.babblelock.acquire()
            services = servdb.read(document)
            for conv in babbler.babblers.values():
                if conv.status == Conversation.GOING_ON:
                    conv.senddata("SUPD", conv.getmessagesequence(), services)
        finally:
            babbler.babblelock.release()
    #--------------------------------------------------------------------------  
    
    config = loadconfiguration()
    babbler = Babblemouth(config)
    
    loadbabblersfromdb(babbler)
    babbler.addhandler("META", metahandler)
    babbler.addhandler("SUPD", servupdhandler)
    babbler.addhandler("SREQ", servreqhandler)
    
    servdb = CouchDBManager("localhost", "5984", "gossip_watchlist")
    servdb.watchdbthreading(processserviceupdate, ["self"])
    
    babbler.start()
    
def startpolicing():
    def processserviceupdate( document ):
    #--------------------------------------------------------------------------
        """
        Handle a update of service list.
        
        Will be called by couchDB change notifier if a babbler's service list is altered
        by receiving a service update. New services are simply queued in the supervisor 
        instance and no longer existing services are removed.
        
        :param document: document which has been altered (passed by CouchDBHandler.watchdbthreading).
        """
        
        try:
            services = simplejson.loads(watchDB.read(document))["services"]
            for index in services:
                service = services[index]
                uid = "%s/%s" % (document, index)
                checker.queueservice(uid, service["proto"], service["ipv4"], service["port"], service["timeout"], 200, 180 )
        except KeyboardInterrupt:
            raise
        except:
            traceback.print_exc()
        finally:
            checker.removeobsoleteservices(document)
    #--------------------------------------------------------------------------    
    
    handler = {"HTTP":HTTPService}
    checker = Supervisor(handler)
    
    try:
        resultDB = CouchDBManager("localhost", "5984", "gossip_watchresults")
        watchDB = CouchDBManager("localhost", "5984", "gossip_watchlist")
        watchDB.watchdbthreading(processserviceupdate, lock=checker.servicelock)
    
        while True:
            
            if not checker.isqueueempty():
                wait = int(checker.getnextschedule() - time.time())
            else:
                wait = 30
        
            if wait <= 0:
                checker.checkservice()
            else:
                resultDB.write("results", checker.getresults())
                resultDB.compact()
                time.sleep(wait)
                ssldebug("%d service(s) currently watched..." % checker.getservicecount())
    finally:
        watchDB.shutdown = True

def start():
    try:
        startgossip()
        time.sleep(2)
        startpolicing()
    except:
        traceback.print_exc()

if __name__ == '__main__':
    start()

