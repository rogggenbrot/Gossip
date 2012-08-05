import couchdb
import simplejson
import threading

class CouchDBManager( object ):
#==============================================================================
    """
    Representation of a service view of a couchDB database. 
    
    >>> db = CouchDBManager("localhost", 5984, "sampledb")
    
    Allows you to read and write documents holding the service list for a 
    distinct peer. Furthermore enables you to receive update messages for
    any document defined.
    """
    
    def getdocumentlist( self ):
    #--------------------------------------------------------------------------
        """
        Return a list of currently available documents in the database.
    
        :return: list containing '_id' of available documents
        """
        documents = []
        for row in self.database.query("function(doc) {emit(doc._id, doc._rev)}"):
            documents.append(row["id"])
            
        return documents
    #--------------------------------------------------------------------------
    
    def __init__( self, host, port, database, createifnone=True ):
    #-------------------------------------------------------------------------- 
        """
        Initalize a CouchDBManager object.
        
        :param host: host name or IP address as string
        :param port: port number on which couchDB is listening
        :param database: name of the database 
        """
        
        url = "http://%s:%s" % (host, str(port))
        try:
            self.database = couchdb.Database("%s/%s" % (url, database))
            self.database.info()
        except:
            if createifnone:
                couchserver = couchdb.Server(url)
                couchserver.create(database)
                self.database = couchdb.Database("%s/%s" % (url, database))
                self.database.info()
                
        self.shutdown = False
    #--------------------------------------------------------------------------

    def read( self, uid ):
    #--------------------------------------------------------------------------
        """
        Read whole document from couchDB. If document doesn't exist or 
        doesn't provide services, an empty service dictionary is returned.
        
        :param uid: '_id' value of the document requested
        :return: dictionary containing all services defined by the document
        """
        
        document = self.database.get(uid)
        
        if document == None:
            return "{}"

        content = ""
        
        for k in document.iterkeys():
            if not k.startswith('_'):
                if isinstance(document.get(k), str):
                    content += '"%s":"%s",' % (k, str(document.get(k)))
                else:
                    content += '"%s":%s,' % (k, str(document.get(k)))
        
        return "{ %s }" % content[:len(content)-1].replace("'", '"')
    #--------------------------------------------------------------------------
    
    def __watchdb( self, handler, documents=None, lock=None ):
    #--------------------------------------------------------------------------
        """
        Establish a watch on certain documents and invoke given handler function
        when receiving a change notification.
        
        This method uses continuous mode as couchDB update feed. As it's run as a 
        thread, it should finally be shut down by setting 'self.shutdown' to 'True'.
        
        :param handler: handler function dealing with the changes (must take 
                        document '_id' as a parameter)
        :param documents: list of documents being watched. 'None' indicates a 
                            watch on 'self' document
        :param lock:    'threading.Lock' or 'threading.RLock' object used to
                        lock resources during update changes
        """
        
        lastseq = 0

        while not self.shutdown:
            changes = self.database.changes(feed="continuous")

            for line in changes:
                if line.has_key("id") and int(line["seq"]) > lastseq and not line.has_key("deleted"):
                    if(documents == None and line["id"] != "self") or (documents != None and line["id"] in documents):
                        try:   
                            if lock is not None:
                                lock.acquire()
                            handler(line["id"])
                            lastseq = int(line["seq"])
                        finally:
                            if lock is not None:
                                lock.release()   
                
                if self.shutdown:       
                    break
    #-------------------------------------------------------------------------- 
        
    def watchdbthreading( self, handler, documents=None, lock=None ):
    #--------------------------------------------------------------------------
        """
        Establish a threaded watch on certain documents and invoke given handler function
        when receiving a change notification.
        
        This method uses continuous mode as couchDB update feed. As it's run as a 
        thread, it should finally be shut down by setting 'self.shutdown' to 'True'.
        
        :param handler: handler function dealing with the changes (must take 
                        document '_id' as a parameter)
        :param documents: list of documents being watched. 'None' indicates a 
                            watch on 'self' document
        :param lock:    'threading.Lock' or 'threading.RLock' object used to
                        lock resources during update changes
        """
        t = threading.Thread(target = self.__watchdb, args = [ handler, documents, lock ])
        t.start()
    #--------------------------------------------------------------------------
    
        
    def write( self, uid, content ):
    #--------------------------------------------------------------------------
        """
        Write received list of services into the according couchDB document.
        
        The invoker of this method should have supremacy to write changes 
        to a service document due to the fact that the method retrieves 
        current '_rev' and retries until it can override existing information
        without raising a couchDB resource conflict. 
        
        ANY PREVIOUS CONTENT OF THE DOCUMENT WILL BE DISCARDED!!!
        
        If the document doesn't exist, a new one will be generated.
        
        :param uid: '_id' of the target document
        :param content: data which will override the previous document body 
        """
        content = simplejson.loads(content)
        document = couchdb.Document()
        document["_id"] = uid
        
        while True:
            try:
                rev = self.database.get(uid)
                
                if rev is not None:
                    rev = rev["_rev"]
                    document["_rev"] = rev
                
                for obj in content:
                    if obj != "_id" and obj != "_rev":
                        document[obj] = content[obj]
                        
                self.database.save(document)
                break
            except couchdb.http.ResourceConflict:
                continue
    #--------------------------------------------------------------------------
#==============================================================================

def ssldebug( msg ):
#--------------------------------------------------------------------------
    """ Prints a messsage to the screen with the name of the current thread """
    print "[%s] %s" % ( str(threading.currentThread().getName()), msg )
    
    return
#--------------------------------------------------------------------------