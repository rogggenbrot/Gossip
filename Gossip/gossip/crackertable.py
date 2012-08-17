'''
Infrastructure for a self-managing peer2peer network with SSL support.
Peers (in the further document called babblemouth or short babbler) 
try to keep a constant conversation with known partners to avoid 
unnecessary SSL handshakes.

@author: Patrick Rockenschaub
'''

import threading
import time
import traceback
import simplejson
import socket
import struct

from M2Crypto import SSL, X509, RSA
from utils import ssldebug


class Babblemouth( threading.Thread ):
#==============================================================================
    """ 
    Representation of a peer point in a local or world-wide network. C
    
    >>> babbler = Babblemouth()
    
    Communicate using SSL connections over TCP sockets. Catalog information
    for up to a given number of conversation partners and listening on a list 
    of given host/port pairs.
    
    Must be provided with a valid X509 certificate containing a unique common 
    name. 
    """
    
    CERTIFICATE_FOLDER = "certificates/known"
    
    def addbabbler( self, identifier, properties, certificate=None ):
    #--------------------------------------------------------------------------
        """ 
        Add a partner name and his characteristics to the known list of babbler.
        
        If maximum number of partners isn't exceeded yet the partner will be added
        to the list. During the processing of the partner the list is locked to 
        avoid anomalies. 
        
        Certificates are only accepted from the certificate owner.
        
        5 different cases may occur:
        
        1. data from 3rd party; not in list yet => 
                        add without verifying (and without certificate)
        2. data from 3rd party; in list but not verified => 
                        override without verifying (and without certificate)
        3. data from 3rd party; in list and verified => 
                        verify version number, update if higher
        4. data form partner => 
                        verify version number, update if higher or 
                        not in list (including certificate)
        5. data from 3rd about myself => 
                        verify if higher, update version number, 
                        increase version number by one if other data doesn't match
        
        :param identifier: canonical name identifying the partner
        :param properties: tupel containing host list, port list, version number and 
                              encrypted version number in this order
        :param certificate: 'M2Crypto.X509' instance, should only be provided if
                            the properties describe the current partner itself, so 
                            there's no doubt that data isn't corrupted.
        :return: 'True' if partner was added, 'False' if an error occured
        """          
        
        try:
            if not properties.has_key("version") or not properties.has_key("c_version"):
                properties["version"] = None
                properties["c_version"] = None
            
            self.babblelock.acquire()
            contact = Contact(properties)
            
            if identifier == self.myid:
                if properties["version"] is None and properties["c_version"] is None:
                    return
                
                cv = decode(contact.c_version, self.x509)
                if cv != properties["version"] or int(cv) <= int(properties["version"]):
                    return
                
                if properties["host"] != self.__config["host"] or properties["port"] != self.__config["port"]:
                    self.__config["version"] = int(properties["version"]) + 1
            
            elif identifier not in self.babblers:
                if self.maxconvsreached():
                    return
                
                self.babblers[ identifier ] = Conversation(self, contact, certificate)
            else:
                conversation = self.getbabbler(identifier)
                conversation.setx509(certificate)
                conversation.setcontact(contact)
        except KeyboardInterrupt:
            raise
        except:
            if self.__config["debug"]:
                traceback.print_exc()
        finally:
            self.babblelock.release()

    #--------------------------------------------------------------------------
    
    def addhandler( self, msgtype, handler ):
    #--------------------------------------------------------------------------
        """ 
        Register a handler for the given message type. Must accept parameter
        'conv' (Conversation) and 'msg' (str).
        
        :param msgtype: 4 character string abbreviation of any msgtype (e.g. 'JSON')
        :param handler: handler method capable of taking 'Babblemouth' instance and 
                        'Conversation' object
        """
        
        assert len(msgtype) == 4
        Conversation.addhandler(msgtype, handler)

    #--------------------------------------------------------------------------
    
    def addrouter( self, router ):
        #--------------------------------------------------------------------------
        """ 
        Register a routing function with this babblemouth. 

        The routing function should take the name of
        a partner (which may not necessarily be present in self.babbler)
        and decide which of the known partners a message should be routed
        to next in order to (hopefully) reach the desired partner. The router
        function should return a tuple of three values: (next-partner-id, host,
        port). If the message cannot be routed, the next-partner-id should be
        None.
        """
        
        self.router = router
        return

    #--------------------------------------------------------------------------
    
    def babblerstojson( self ):
    #--------------------------------------------------------------------------
        """
        Return a JSON object containing network information about myself and all
        known babblers.
        
        :return: JSON object as string
        """
        
        c_version = encode(self.__config["version"], self.__privatekey)
        
        content = '{"%s":{"host":%s, "port":%s, "version":%d, "c_version":"%s"}' \
                    % (self.myid, self.__config["host"], self.__config["port"],   \
                       self.__config["version"], c_version) 
        content = content.replace("'", '"')
        
        for identifier in self.babblers:
            content += ', "%s":%s' % (identifier, self.babblers[identifier].contact.tojson())        
        
        return content + '}'
    #--------------------------------------------------------------------------
    
    def getbabbler( self, identifier ):
    #--------------------------------------------------------------------------
        """
        Return the conversation object for the given common name.  
        
        :param identifier: canonical name identifying the partner.
        :return: instance of 'Contact' class. Contact will be only
                    initialized as with 'None' if babbler not in list.
        """
        
        if self.babblers.has_key(identifier):
            return self.babblers.get(identifier)
        
        return None

    #-------------------------------------------------------------------------    
    def __init__( self, config ):
    #--------------------------------------------------------------------------
        """ 
        Initialize a babbler. 
        
        Must be provided with all necessary configuration data stored in a dict:
        - 'host': list of IP addresses or DNS names
        - 'port': list of port numbers mapped (mapped to host by list index)
        - 'maxconv': number of maximum conversations at a time (0 for infinite)
        - 'debug': enable debug output by passing 1
        - 'verbose': enable verbose output by passing 1
        - 'certificate': dictionary containing 'key':'KEY_FILE_PATH', 'certificate':
                            'CERT_FILE_PATH', 'ca':'CA_CERT_FILE_PATH'
        
        
        Create a 'M2Crypto.X509' object and extract the common name specified
        in the certificate as own identifier.
        
        Furthermore try to load already known babblers. 
        """
        threading.Thread.__init__(self)

        self.__config = config

        # the canonical id is defined as common name in the provided certificate 
        self.x509 = X509.load_cert(self.__config["certificates"]["certificate"], X509.FORMAT_PEM)
        self.myid = str(self.x509.get_subject().get_entries_by_nid(13)[0].get_data())    # 13 is the nid for common name
        self.__privatekey = RSA.load_key(self.__config["certificates"]["key"])     
        
        self.babblers = {} 
        self.babblelock = threading.RLock()
    
        self.handlers = {}
        self.router = None
        self.addrouter(self.routeviatable)

        self.shutdown = False  # use to stop the main loop

    #--------------------------------------------------------------------------
    
    def listen( self, host, port ):
    #--------------------------------------------------------------------------
        '''
        Create a server socket and bind it to the given host/port. For every incoming
        connection a SSL tunnel will be established. Either babbler connects for the first
        time respectively conversation is currently ended a conversation is starting, or 
        conversation will be dismissed (to avoid multiple connections to the same peer).
        
        The server connection will timeout every 60 seconds in order to check for 
        the shutdown flag. 
        
        :param host: DNS name or IP address to listen
        :param port: port number to listen
        '''
        
        s = self.makeserversocket( host, port )
        s.set_socket_read_timeout(SSL.timeout(60))
        
        self.__verbose( 'Listening for conversation invitations on %s:%d' % ( host, port ) ) 
        
        while not self.shutdown:          
            try:
                clientsock, _ = s.accept()
                
                self.__verbose( 'Talking to %s' % str(clientsock.getpeername()) )
    
                # open a new ssl conversation with the requesting peer
                host, port = clientsock.getpeername()
                contact = Contact({"host":[host],"port":[port], "version":None, "c_version":None})
                
                conv = Conversation(self, contact, None)
                conv.setsocket(clientsock)
                conv.buildssl()
                
                if conv.id in self.babblers: 
                    if self.getbabbler(conv.id).status == Conversation.ENDED:
                        self.getbabbler(conv.id).setsocket(conv.s)
                        self.getbabbler(conv.id).setx509(conv.x509)
                        self.getbabbler(conv.id).id = conv.id
                        self.getbabbler(conv.id).start()
                    else:
                        conv.end()
                else:
                    self.babblers[conv.id] = conv
                    conv.start()
                    
            except Exception:
                pass
                #if self.__config["debug"]:
                    #traceback.print_exc()
        
        self.__verbose( 'Stop listening on %s:%d' % ( host, port ) )
        s.close()
        
    #--------------------------------------------------------------------------
    
    def loadbabbler( self, identifier, data, forconv = None ):
    #--------------------------------------------------------------------------
        """
        Load babblers into 'self.babblers' by parsing string via simplejson 
        and repeatedly calling 'self.addbabbler'.
        
        Can be revoked in two modes: either by passing a conversation indicating
        a babbler who shares his list of babblers with us or by leaving the conversation
        to 'None' which indicates that the babblers are loaded from disk.
        
        If the babblers are received over the network, only the certificate 
        of the communication partner is forwarded, for it's the only one we 
        can be sure isn't corrupted. On other hand if loaded from the disk
        we already validated the certificate before storing so we can pass it on.
        
        :param s: JSON object as string containing the babblers
        :param forconv: conversation which provides the babblers
        """
            
        if forconv == None:     # load from disk => pass certificates on for we need them later to check versions
            try:
                x509 = X509.load_cert("%s/known/%s.pem" % (Babblemouth.CERTIFICATE_FOLDER, identifier), X509.FORMAT_PEM)
            except:
                x509 = None
        else:       # we receive the data over network, ignore any provided certificates
            x509 = None
        
        # Depending on whether it's data about the communication partner,
        # myself or 3rd party data, pass on different certificates (often
        # 'None')
        if forconv != None and identifier == forconv.id:
            self.addbabbler(identifier, data, forconv.x509)
        elif identifier == self.myid:
            self.addbabbler(identifier, data, self.x509)
        else:
            self.addbabbler(identifier, data, x509)
                
    #-------------------------------------------------------------------------- 
    
    def makeserversocket( self, host, port):
    #--------------------------------------------------------------------------
        """ 
        Construct and prepare a SSL server socket listening on the given port.
        Uses the certificates defined for this server.
        
        :param host: DNS name or IP address to listen
        :param port: port number to listen
        :return: SSL socket listening for incoming requests
        """
        
        s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
        s.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, "port" )
        
        context = getcontext(self.__config["certificates"])

        ssl = SSL.Connection(context, s)
        ssl.bind((host, port))
        ssl.listen()
        
        return ssl
    #--------------------------------------------------------------------------
    
    def maxconvsreached( self ):
    #--------------------------------------------------------------------------
        """ 
        Return whether the maximum limit of names has been added to the
        list of known babblers. Always returns True if maxconv is set to
        0.
        
        :return: 'True' if the maximum amount of conversations is reached,
                    'False' otherwise
        """
        
        assert self.__config["maxconv"] == 0 or self.numberofbabblers() <= self.__config["maxconv"]
        return self.__config["maxconv"] > 0 and self.numberofbabblers() == self.__config["maxconv"]

    #--------------------------------------------------------------------------
    
    def numberofbabblers( self ):
    #--------------------------------------------------------------------------
        """ 
        Return the number of known babblers. 
        """
        return len(self.babblers)
    
    #--------------------------------------------------------------------------

    def __restartconversations( self ):
    #------------------------------------------------------------------------- 
        """
        Try to restart conversations with known but not connected conversation
        partner.
        """
        if self.shutdown:
            return
        
        self.__verbose("%d Threads alive" % threading.active_count())
        
        for identifier in self.babblers:
            if self.getbabbler(identifier).status == Conversation.ENDED:
                t = threading.Thread(target=self.talktobabbler, args=[identifier])
                t.start()
                
    #------------------------------------------------------------------------- 

    def routeviatable( self, identifier):
    #--------------------------------------------------------------------------
        """
            Route to the identifier by just looking up the address in 'self.babblers'.
            
            :param identifier: canonical name identifying the partner
        """
        
        return self.getbabbler(identifier)
    #--------------------------------------------------------------------------
      
    def run( self ):
    #--------------------------------------------------------------------------
        """
        Start one server per host/port pair defined in configuration file. Every
        server will be started in a separate thread but uses the same babbler list.
        
        Every 60 seconds inactive threads will be restarted.
        
        Will be executed when start() is called. Terminate by setting 'self.shutdown'
        to 'True'.
        """
        
        for server in range(0, len(self.__config["host"])):
            t = threading.Thread( target = self.listen,
                                  args = [self.__config["host"][server], self.__config["port"][server]] )
            t.start()
            
        while not self.shutdown:
            self.__restartconversations()
            
            time.sleep(60)

    #--------------------------------------------------------------------------
    
    def talktobabbler( self, identifier ):
    #--------------------------------------------------------------------------
        '''
        Establish a conversation with the passed partner by using the registered 
        routing method. The communication will be handeld by the conversation 
        object related to the babbler. 
        
        :param identifier:  canonical name identifying the partner
        :return: 'False' if there's no routing method known for the requested partner, 
                    otherwise 'True'
        '''
        
        if identifier in self.babblers and self.getbabbler(identifier).status != Conversation.ENDED:
            return 
        
        if self.router:
            conv = self.router( identifier )
        if not self.router or conv is None:
            self.__verbose( 'Unable to route to %s' %  identifier )
            return 
           
        try:    
            if conv.status == Conversation.ENDED:
                conv.setsocket(None)
                conv.setcontext(getcontext(self.__config["certificates"]))
                conv.buildssl()
                conv.start()
        except:
            self.__verbose("%s is currently not available" % identifier)
            #if self.__config["debug"]:
                #traceback.print_exc()
      
    #--------------------------------------------------------------------------
    
    def __verbose( self, msg ):
    #--------------------------------------------------------------------------
        """
        Print message if verbose flag is set. Meant for messages which indicate 
        what the object is doing right now without including information 
        necessary for debugging (e.g. no error messages but connection status)
        
        :param msg: string containing information
        """
        
        if self.__config["verbose"]:
            ssldebug( msg )

    #--------------------------------------------------------------------------
    
#==============================================================================










class Conversation( object ):
#==============================================================================
    """
    Representation of a communication held with a remote partner.
    
    >>> conv = Conversation("1.2.3.4", 40000, ("key.pem", "certificate.pem", "ca.pem"))
    
    At each point in time a conversation is in a definite state which
    can either be ENDED, DISMISSING (shutting down) or GOING_ON.
    
    """
    
    ENDED = 0
    GOING_ON = 1
    DISMISSING = 2
    
    __msghandler = {}
    
    def addhandler( msgtype, handler ):
    #--------------------------------------------------------------------------
        """ 
        Register a handler for the given message type.
        
        :param msgtype: 4 character string abbreviation of any msgtype (e.g. 'JSON')
        :param handler: handler method capable of taking 'Conversation' instance and 
                        message content as 'str'.
        """
        
        assert len(msgtype) == 4
        Conversation.__msghandler[ msgtype ] = handler

    #--------------------------------------------------------------------------
    
    addhandler = staticmethod(addhandler)
    
    def buildssl( self ):
    #--------------------------------------------------------------------------    
        """
        Establish a SSL connection to remote partner and initialize certificate
        object and remote common name for current conversation.
        
        If socket object isn't set a new TCP socket will be created. Therefore 
        a SSL context must have been provided earlier, otherwise a ValueError
        will be raised.
        
        :raise RuntimeError: if conversation is still going on
        :raise ValueError: if neither a TCP socket nor a SSL context have been provided.
        """
        
        if self.status != Conversation.ENDED:
            raise RuntimeError("Conversation still running or shutting down.")
        elif self.s is None and self.context is None:
            raise ValueError("Either socket or SSL context must be provided.")
        
        ssldebug("Introduce to %s:%d" % (self.contact.hosts[self.hostindex], self.contact.ports[self.hostindex]))
    
        if not self.s:
            sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
            
            self.s = SSL.Connection(self.context, sock)
            self.s.set_post_connection_check_callback(None)
            self.s.connect( ( self.contact.hosts[self.hostindex], self.contact.ports[self.hostindex] ) )
            
        self.x509 = self.s.get_peer_cert()   
        self.id = str(self.x509.get_subject().get_entries_by_nid(13)[0].get_data())     # 13 is the nid for 'commonName'
    #--------------------------------------------------------------------------   
    
    def end( self ):
    #--------------------------------------------------------------------------
        """
        Shut down the conversation.
        """
        if self.status == Conversation.GOING_ON:
            self.status = Conversation.DISMISSING
            self.sendqueue = []

    #--------------------------------------------------------------------------
    
    def getmessagesequence( self ):
    #--------------------------------------------------------------------------
        """
        Return current sequence number for this conversation and increment it 
        afterwards.
        
        :return: current sequence number as integer
        """
        
        self.__msgseq += 1
        return self.__msgseq
    #--------------------------------------------------------------------------
    
    def __incrementhostindex( self ):
    #--------------------------------------------------------------------------
        """
        Increment the internal count defining the position in the host list to look
        at. Varies between 0 and len(host) - 1.
        """
        
        self.hostindex = (self.hostindex + 1) % len(self.contact.hosts)
    #--------------------------------------------------------------------------
        
    def __init__( self, babblemouth, contact, x509=None ):
    #--------------------------------------------------------------------------
        """
        Initialize conversation object.
        
        :param babblemouth: owner of the conversation object (instance of 'Babblemouth')
        :param contact: contact details of the communication parner
        :param x509: peer certificate
        """
        
        self.__msgseq = 0
        self.hostindex = 0
        self.status = Conversation.ENDED
        self.__sendqueue = []
        self.id = None
        
        self.babblemouth = babblemouth
        self.x509 = x509
        self.setsocket(None)
        self.setcontact(contact)

    #--------------------------------------------------------------------------

    def __makemsg( self, msgtype, msgseq, msgdata ):
    #--------------------------------------------------------------------------
        """
        Wrap message with meta data.
        
        :param msgtype: 4 character abbreviation for a message type
        :param msgseq: ongoing number to be able to put messages in order
        :param msgdata: string data which should be packed
        :return: packed message as struct
        """
        
        msglen = len(msgdata)
        msg = struct.pack( "!4sii%ds" % msglen, msgtype, msglen, msgseq, msgdata )
        return msg

    #--------------------------------------------------------------------------

    def processmessage( self, msgtype, msg ):
    #--------------------------------------------------------------------------
        """
        Check if there's a registered handler for the given message type 
        and call it if possible.
        
        :param conv: conversation which should be handled
        :param msgtype: 4 character message type abbreviation
        :raise ValueError: if there's no handler for this specific message type
                            registered
                            
        """
        
        if msgtype: msgtype = msgtype.upper()
        if msgtype not in Conversation.__msghandler:
            return
        
        Conversation.__msghandler[ msgtype ]( self, msg )   

    #--------------------------------------------------------------------------

    def __recvdata( self ):
    #--------------------------------------------------------------------------
        """
        Receive a message from a conversation. Returns (None, None, None)
        if there had been any error.
        
        :return: tupel containing message type, sequence and data
        :raise KeyboardInterrupt: if a KeyboardInterrupt is encounteredlll
        """
    
        msgtype = self.s.read( 4 )
        if not msgtype: return (None, None, None)
        
        lenstr = self.s.read( 4 )
        msglen = int(struct.unpack( "!i", lenstr )[0])
        seqstr = self.s.read( 4 )
        msgseq = int(struct.unpack( "!i", seqstr )[0])
        msg = ""

        while len(msg) != msglen:
            data = self.s.read( min(2048, msglen - len(msg)) )
            if not len(data):
                break
            msg += data
    
        if len(msg) != msglen:
            return (None, None, None)
    
        return ( msgtype, msgseq, msg )

    #--------------------------------------------------------------------------
    
    def run( self ):
    #--------------------------------------------------------------------------
        """
        Start actual conversation and handle appearing errors. A conversation 
        always begins with a push of current hold contact data to other
        babblers to keep the network up to date.
        """
        try:
            self.settimeout(30)
            self.status = Conversation.GOING_ON
        
            self.senddata("META", self.getmessagesequence(), self.babblemouth.babblerstojson())
            self.__senddata()
            self.__talk()
        except SSL.SSLError:
            pass
        except:
            traceback.print_exc()
        finally:
            try:
                self.s.close()
            except:
                self.__incrementhostindex()
            finally:
                self.setsocket(None)
            
            ssldebug("%s:%d is in no mood to talking" % (self.contact.hosts[self.hostindex], self.contact.ports[self.hostindex]))
            self.status = Conversation.ENDED
    #--------------------------------------------------------------------------

    def senddata( self, msgtype, msgseq, msgdata ):
    #--------------------------------------------------------------------------
        """
        Send a message through the conversation. Packs the message before
        sending. Conversation must be going on in order to send data.
        
        :param msgtype: 4 character abbreviation for a message type
        :param msgseq: ongoing number to be able to put messages in order
        :param msgdata: string data which should be packed
        """
    
        if self.status is not Conversation.GOING_ON:
            return 
        
        msg = self.__makemsg( msgtype.upper(), msgseq, msgdata )
        self.__sendqueue.append(msg)
        
    #--------------------------------------------------------------------------
    
    def __senddata( self ):
    #--------------------------------------------------------------------------
        """
        Iterate over queued data and send it.
        
        :return: 'True' if data successfully sent, 'False' otherwise
        """
    
        while len(self.__sendqueue) > 0:
            msg = self.__sendqueue.pop(0)
            self.s.write( msg )
        return True
        
    #--------------------------------------------------------------------------

    def setcontact( self, contact ):        
    #--------------------------------------------------------------------------
        """
        Update contact data of this conversation. Sanity checks ensure that only 
        new or more accurate data is stored.
        
        :param contact: 'Contact' object containing new data.
        :return: True if an update has been made, False otherwise.
        :raise TypeError: If anything other than a 'Contact' object is passed.
        """
        
        if not isinstance(contact, Contact):
            raise TypeError("Parameter 'contact' must be of type 'Contact'")
        
        if self.x509 == None:
            self.contact = contact
            return True
        elif contact.c_version == None:
            return False

        # check if version and checkversion match and if new version is higher
        cv = decode(contact.c_version, self.x509)
        if self.contact.version != None and (cv != contact.version or int(cv) <= int(self.contact.version)):
            return False
        
        self.contact = contact
    #--------------------------------------------------------------------------

    def setcontext( self, context ):
    #--------------------------------------------------------------------------
        """
        Set a new SSL context for this conversation.
        """
        
        self.context = context
    #--------------------------------------------------------------------------

    def setsocket( self, sock ):
    #--------------------------------------------------------------------------
        """
        Set a new socket object for this conversation.
        """
        
        self.s = sock
    #--------------------------------------------------------------------------
    
    def settimeout( self, seconds ):
    #--------------------------------------------------------------------------
        """
        Call the settimeout method of the SSL connection which passes it 
        to the underlying socket.
        
        :param seconds: timeout in seconds
        """
        
        self.s.set_socket_read_timeout(SSL.timeout(seconds))
    #--------------------------------------------------------------------------
    
    def setx509( self, x509 ):
    #--------------------------------------------------------------------------
        """
        Set a new certificate object. Will not override current known 
        certificate with 'None'.
        """
        if x509 is None and self.x509 is not None:
            return 
        
        self.x509 = x509
    #--------------------------------------------------------------------------
   
    def start( self ):
    #--------------------------------------------------------------------------
        """
        Starts conversation in a new thread. 
        
        :raise RuntimeError: if conversation status is anything else but ENDED.
        """
        
        if self.status != Conversation.ENDED:
            raise RuntimeError("Conversation is still going on, can't call start().")
        
        t = threading.Thread(target=self.run)
        t.start()
    #--------------------------------------------------------------------------
   
    def __talk( self ):
    #--------------------------------------------------------------------------    
        """
        Communicate with another babbler. 
        
        Connection will be closed if any SSL error occurs or partner takes to 
        long to answer (over 60 seconds). Will check sendqueue every 20 
        seconds for data to send or will make heartbeat otherwise.
        """
        
        lastmsg = time.time()
        
        while self.status == Conversation.GOING_ON:
                try:                
                    msgtype, _, msgdata = self.__recvdata()
                    
                    if msgtype is None:
                        raise Exception("Time out to watch ")
                    else:
                        ssldebug("Got %s from %s" % (msgtype, self.id) )
                        self.processmessage(msgtype, msgdata)
                        lastmsg = time.time()
                    
                    self.__senddata()
                except KeyboardInterrupt:
                    raise
                except SSL.SSLError:
                    self.status = Conversation.DISMISSING
                    ssldebug("%s ended because of an error during connection" % self.id)
                except:
                    traceback.print_exc()
                    
                    if time.time() - lastmsg > 60 or self.status != Conversation.GOING_ON:
                        ssldebug("%s needed to long to answer" % self.id)
                        self.status = Conversation.DISMISSING
                        continue
                    
                    if len(self.__sendqueue) == 0:
                        self.senddata("HRTB", self.getmessagesequence(), "Heartbeat")
                        
                    self.__senddata()
                    time.sleep(20)      
    #--------------------------------------------------------------------------

#==============================================================================





  
class Contact( object ):
#==============================================================================
    '''
    Represents the properties of a known babblemouth.
    '''
    
    def __init__( self, data ):
    #--------------------------------------------------------------------------
        """
        Initalize a Contact by setting all the necessary data.
        
        :param data: tupel consisting of host, port, version number and private key encoded version number
        :param certificate: instance of X509 certificate used to decode version number
        """
        self.setvalues(data)   # add certificate to complete tupel
    #--------------------------------------------------------------------------

    def setvalues( self, data ):
    #--------------------------------------------------------------------------
        """
        Override existing values with new ones.
        
        :param host: DNS name or IP address
        :param port: port number on which the conversation is held
        :param version: current version of the contact tupel (indicates how often it has
                            changed and which is the newer contact information
        :param c_version: private key encoded version file in order to guarantee 
                            the data is originally from the babbler described by this 
                            contact object.
        """
        
        self.hosts = data["host"]
        self.ports = data["port"]
        self.version = str(data["version"]) if data["version"] != None else None
        self.c_version = str(data["c_version"]) if data["c_version"] != None else None
    #--------------------------------------------------------------------------   
     
    def tojson ( self ):
    #--------------------------------------------------------------------------
        """
        Return JSON object containing host, port, version and checkversion.
        
        :return: JSON object as string
        """
        if self.version == None or self.c_version == None:
            return simplejson.dumps({"host":self.hosts, "port":self.ports}, indent=2)
        
        return simplejson.dumps({"host":self.hosts, "port":self.ports, "version":self.version, "c_version":self.c_version}, indent=2)
    #--------------------------------------------------------------------------
#==============================================================================



def decode(msg, certificate):
#--------------------------------------------------------------------------
    """
    Decode a given message using the public key of a PEM certificate.
    
    :param msg: hex encrypted text message to be decoded
    :param certificate: instance of M2Crypto.X509 object (PEM encoded)
    :return: decoded message as 'str'.
    """
    pub = certificate.get_pubkey().get_rsa()
    return pub.public_decrypt(msg.decode('hex'), RSA.pkcs1_padding)

#--------------------------------------------------------------------------

def encode(msg, key):
#--------------------------------------------------------------------------
    """
    Decode a given message using the public key of a PEM certificate.
    
    :param msg: plain text message to be encoded
    :param key: instance of M2Crypto.RSA.RSA object (private key)
    :return: encoded message as 'str' in hex formate.
    """
    return str(key.private_encrypt(str(msg), RSA.pkcs1_padding).encode('hex'))
#--------------------------------------------------------------------------

def getcontext( certs ):
#--------------------------------------------------------------------------
    '''
    Build up a SSL context using the certificat tupel (keyfile, certfile, cafile)
    passed as parameter. 
    
    Use Transport Layer Security Protocol and requires peer certificate as well
    (both sides of the connection must provide a certificate)
    
    :param certs: certificat tupel (KEY_FILE_NAME, CERT_FILE_NAME, CA_CERT_FILE_NAME)
    '''                
    context = SSL.Context(protocol='tlsv1')

    # load certificate stuff.
    context.load_cert(certfile=certs["certificate"], keyfile=certs["key"])
    context.load_verify_locations(cafile=certs["ca"])
    context.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, 1)
    
    return context
#--------------------------------------------------------------------------