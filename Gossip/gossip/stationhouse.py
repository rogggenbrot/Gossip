'''
Created on Jul 24, 2012

@author: Patrick Rockenschaub
'''

import heapq
import threading
import time
import urllib

class Supervisor(object):
#===========================================================l===================
    """
    Representation of an service supervisor. 
    
    >>> sup = Supervisor()
    
    Manages a queue of services ordered by the scheduled time for their next
    execution. Allows to define a handler for any desired protocol type. The 
    handler therefore has to be a subclass of 'services.Service' and must
    override the '_police()' method in order to work properly.
    """

    def __init__( self, handler ):
    #--------------------------------------------------------------------------
        """
        Initialize the service supervisor object. Registers given handler functions
        and creates a service list and a related RLock object.
        
        :param handler: map of protocol name to according handler object
        """
        self.servicehandler = {}
        
        for protocol in handler:
            self.sethandler(protocol, handler[protocol])
            
        self.sethandler("UNKNOWN", Service)
        
        self.services = []
        self.servicelock = threading.RLock()
    #--------------------------------------------------------------------------


    def __gethandler( self, protocol ):
    #--------------------------------------------------------------------------
        """
        Return new instance of the handler object related with the given 
        protocol shortcut.
        
        :param protocol: shortcut determining the protocol (e.g. 'HTTP')
        :return: instance of handler object
        """
        
        if protocol.upper() in self.servicehandler:
            return self.servicehandler[protocol]()
        
        return self.servicehandler["UNKNOWN"]()
    #--------------------------------------------------------------------------
    
    def __getnextservice( self ):
    #--------------------------------------------------------------------------
        """
        Return next service in queue which has the be checked. Lock service
        list during the whole progress to avoid anomalies. 
        
        :return: next service in row, already initialized with all necessary
                    information            
        """
        
        try:
            self.lock()
            service = heapq.heappop(self.services)[1]
        except KeyboardInterrupt:
            raise
        except:
            return None
        finally:
            self.release()
        
        return service
    #--------------------------------------------------------------------------

    def __newservice( self, uid, protocol, host, port, timeout, pattern, interval ):
    #--------------------------------------------------------------------------
        """
        Returns new handler instance for given service type already initialized with
        necessary information.

        :param uid: unique identifier (e.g. a combination of host, port and service)
        :param protocol: abbreviation of the protocol necessary to communicate with 
                            the service
        :param host: host name as a string
        :param port: port where service is listening
        :param timeout: time period after which service will presumed as faulty
        :param pattern: string to look for in the service response (mismatch
                        may indicate a fault)
        :param interval: periodically check service again after given number in seconds 
                        
        """
        
        service =  self.__gethandler(protocol)
        service.setbasicvalues(uid, protocol, host, port, timeout, pattern, interval)
        
        return service
    #--------------------------------------------------------------------------
    
    def __queueservice( self, service, newflag = 0 ):
    #--------------------------------------------------------------------------
        """
        Insert given service in priority queue. A item contained by the priority 
        queue consists of it's next scheduled time, the properly set handler object 
        and an 'outdated' flag. 
        
        The flag indicates if the service is still present in the last service list
        received. Outdated services are removed by calling 'self.removeobsoleteservices'.
        
        The service list is locked the whole time to avoid anomalies. If the service is
        already present in the service list, it is just updated without touching the 
        scheduled time. Otherwise it's added to the list.
        
        :param service: handler object representing a single service
        :param newflag: indicate if the service was newly added or just requeued
        """
        try:
            self.lock()
            
            if service in self.services:
                pos = self.services.index(service)
                self.services[pos][1].setbasicvalues(service.uid, service.protocol, service.host, service.port, service.timeout, service.pattern, service.interval)
                self.services[pos][2] = newflag
            else:
                heapq.heappush(self.services, [(service.lastschedule + time.time()), service, newflag])   
        finally:
            self.release()
    #--------------------------------------------------------------------------
    
    def checkservice( self ):
    #--------------------------------------------------------------------------
        """
        Check next service and requeue it.
        """
        try:
            self.lock()
            
            service = self.__getnextservice()
            if service is not None:
                service.police()
                self.__queueservice(service)
        finally:
            self.release()
    #--------------------------------------------------------------------------  
    
    def getnextschedule( self ):
    #--------------------------------------------------------------------------
        """
        Return the scheduled time of the first object in the queue. In case of an 
        empty service queue the current time will be returned. 
        
        :return: next scheduled time as unix time stamp
        """
        
        try:
            self.lock()
            
            if self.isqueueempty():
                return time.time()
            
            service = self.services[0][1]
        finally:
            self.release()
        
        return service.lastschedule + service.interval
    #--------------------------------------------------------------------------  
    
    def getresults( self ):
    #--------------------------------------------------------------------------  
        try:
            self.lock()
            
            results = " "
            
            for s in range(0,len(self.services)):
                results += '["%s", %f, %s, %d],' % \
                              (self.services[s][1].uid, self.services[s][1].lastschedule, int(self.services[s][1].laststatus), self.services[s][1].timeout) 
                              
            return '{"results":[ %s ]}' % results[:len(results)-1]
        finally:
            self.release()
    #--------------------------------------------------------------------------  
    
    def getservicecount( self ):
    #--------------------------------------------------------------------------
        """
        Return the amount of services currently enqueued.
        
        :return: length of service list
        """
        return len(self.services)
    #--------------------------------------------------------------------------
    
    def lock( self ):
    #--------------------------------------------------------------------------
        """
        Lock service list for everyone except the own thread (RLock).
        """
        
        self.servicelock.acquire()
    #--------------------------------------------------------------------------
    
    def isqueueempty( self ):
    #--------------------------------------------------------------------------
        """
        :return: 'True' if service list is empty, 'False' otherwise
        """
        
        if len(self.services) == 0:
            return True
        
        return False
    #--------------------------------------------------------------------------
    
    def queueservice( self, uid, protocol, host, port, timeout, pattern, interval ):
    #--------------------------------------------------------------------------
        """
        Insert a service defined by an external source into the queue. Therefore a new
        handler is initialized and forwarded to the private '__queueservice' function.
        
        :param uid: unique identifier, should allow the aggregation of belonging services
                        by starting with an group id (e.g. starting with host:port)
        :param protocol: abbreviation of the protocol necessary to communicate with 
                            the service
        :param host: host name as a string
        :param port: port where service is listening
        :param timeout: time period after which service will presumed as faulty
        :param pattern: string to look for in the service response (mismatch
                        may indicate a fault)
        :param interval: periodically check service again after given number in seconds 
        """
        
        service = self.__newservice(uid, protocol, host, port, timeout, pattern, interval)
        self.__queueservice(service, newflag = 1)
    #--------------------------------------------------------------------------
    
    def release( self ):
    #--------------------------------------------------------------------------
        """
        Release a currently hold lock of the service list.
        """
        self.servicelock.release()
    #--------------------------------------------------------------------------   
    
    def removeobsoleteservices( self, groupidentifier ):
    #--------------------------------------------------------------------------
        """
        Remove outdated services still present in the service list. 
        
        Lock the list for the length of the method. Store all outdated services
        in a separate list and remove them after the search to avoid messing the
        iterator up. All 'outdated' flags are reseted.
        
        :param groupidentifier: unique id partly shared in the uid of belonging
                                services
        """
        
        rmlist = []
        try:
            self.lock()
            for service in self.services:
                if service[1].uid.startswith(groupidentifier):
                    if service[2] == 0:
                        rmlist.append(service)
                    else:
                        service[2] = 0
                    
            for service in rmlist:
                self.services.remove(service)
        finally:
            self.release()
    #--------------------------------------------------------------------------
    
    def sethandler( self, protocol, handler ):
    #--------------------------------------------------------------------------
        """
        Register a handler class for a specific protocol type.
        
        :param protocol: string abbreviation of the protocol
        :param handler: handler class related to the given protocol
        """
        
        self.servicehandler[protocol] = handler
    #--------------------------------------------------------------------------
#==============================================================================






class Service( object ):
#==============================================================================
    """
    Representation of a basic service.

    >>> service = Service()

    This class should be used for unknown protocol types. Service handler 
    should inherit the behavior and override the _police() method.

    A Service class and it's subclasses are identified by a unique identifier
    stored in self.uid
    """
    
    def __init__( self ):
    #--------------------------------------------------------------------------
        """
        Initialize the service object.

        Creates a dummy, actual data has to be set using the setvalues(...) method.
        """

        
        self.protocol = "UNKNOWN"
        self.host = "localhost"
        self.port = 0
        self.timeout = 0
        self.pattern = ""
        self.lastschedule = time.time()
        self.laststatus = -1
        self.interval = 999999999       # unknown service should only be
                                        # controlled once in order to 
                                        # indicate the missing specification
    #--------------------------------------------------------------------------
    
    def __eq__(self, other):
    #--------------------------------------------------------------------------
        """
        Two subclasses of 'Service' are equal if their 'uid' is euqal.
        
        :return: 'True' if the uids are euqal, 'False' otherwise
        :raise TypeError: if the given object is not instance of the same
                            class
        """
        
        if isinstance(other[1], self.__class__):
            return self.uid == other[1].uid
        
        raise TypeError("Expected instance of 'Service' or subclass")
    #--------------------------------------------------------------------------
    
    def _police( self ):
    #--------------------------------------------------------------------------
        """
        Dummy method used for unknown protocol types. While always announce a 
        fault in order to indicate the missing information.
        
        Should be overridden by more precise service handler.
        """
        
        self.laststatus = False
    #--------------------------------------------------------------------------
    
    def police( self ):
    #--------------------------------------------------------------------------
        """
        Starts _police() method in new thread.
        
        :return: running instance of 'threading.Thread'
        """
        
        self.lastschedule = time.time()
        t = threading.Thread(target=self._police, args = [ ])
        t.start()
        
        return t
    #--------------------------------------------------------------------------    
    
    def setbasicvalues( self, uid, protocol, host, port, timeout, pattern, interval):
    #--------------------------------------------------------------------------
        """
        Initialize the server object.

        :param uid: unique identifier (e.g. a combination of host, port and service)
        :param protocol: abbreviation of the protocol necessary to communicate with 
                            the service
        :param host: host name as a string
        :param port: port where service is listening
        :param timeout: time period after which service will presumed as faulty
        :param pattern: string to look for in the service response (mismatch
                        may indicate a fault)
        :param interval: periodically check service again after given number in seconds 
                        
        """
        
        self.uid = uid
        self.protocol = protocol
        self.host = host
        self.port = str(port)
        self.timeout = timeout
        self.pattern = pattern
        self.interval = interval
    #--------------------------------------------------------------------------
    
#==============================================================================





class HTTPService( Service ):
#==============================================================================
    """
    Representation of a HTTP service.

    >>> httpserv = HTTPService()

    Checks the availability of an HTTP service at the given host name and port.
    If the response code matches the given pattern (e.g. '200' for OK) the 
    service is considered to be alright, otherwise a fault is presumed.
    """
    
    def __init__( self ):
    #--------------------------------------------------------------------------
        """
        Initialize the HTTPService object.

        Creates a dummy, actual data has to be set using the setvalues(...) method.
        """
        Service.__init__(self)
    #--------------------------------------------------------------------------
    
    def _police( self ):
    #--------------------------------------------------------------------------
        """
        Uses urllib to make a HTTP GET request to own host name and port. If the
        response code matches the pattern, the service is considered to be alright.
        """
        try:
            response = urllib.urlopen("http://" + self.host + ":" + str(self.port)).getcode()
            self.laststatus = response == self.pattern
        except KeyboardInterrupt:
            raise
        except:
            self.laststatus = False
    #--------------------------------------------------------------------------
    
#==============================================================================