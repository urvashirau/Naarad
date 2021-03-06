import os, tempfile;#, threading;
from threading import Thread,Condition;
import settings5;
import NaaradUtils as Utils;
import select;
import socket;

class NaaradClientException(Exception):
    pass;

#
# Object to service a socket connection.  The implementation of this
# class has to be in this file since one of its methods access the
# global variable topicsSubscriberList.
class ClientThread (Thread):
    #
    #--------------------------------------------------------------------------
    #
    def __init__(self, threadID, name, clientsocket, uno, pogo, connectiontype=""):
        Thread.__init__(self)
        self.threadID = threadID;
        self.name = name;
        self.myc1 = clientsocket;
        self.uno  = uno;
        self.pogo = pogo;
        cTypeStr = connectiontype.strip();
       # self.makeNamedPipe();
    #
    #--------------------------------------------------------------------------
    #
    def makeNamedPipe(self):
        self.tmpdir = tempfile.mkdtemp(prefix="/dev/shm/")
        self.filename = os.path.join(self.tmpdir, 'myfifo')
        print (self.name+" creating "+self.filename);
        try:
            os.mkfifo(self.filename)
        except OSError as e:
            print("Failed to create FIFO: %s" % e);
        else:
            self.pPogoListen = open(self.filename, 'r+');
            self.pogo.addListeningPort(self.pPogoListen.fileno());
    #
    #--------------------------------------------------------------------------
    #        
    def closeSock(self,sock,msg=None):
        if (msg != None):
            print(msg);
        sock.shutdown(1);
        sock.close();
    #
    #--------------------------------------------------------------------------
    #        
    def getNodeList(self,tok):
        nodeList=[];
        for keys in settings5.gPacketHistory:
            if (isinstance(keys,tuple)):
                nodeList.append(keys[0]);
            else:
                nodeList.append(keys);
        # Convert the list to a list of unique elements
        nodeList=list(set(nodeList));
        print("nodeList=",nodeList);
        pass;
    #
    #--------------------------------------------------------------------------
    #        
    def getParamList(self,tok):
        print("getParamList: ",tok);
        paramList=[];
        if (len(tok) < 2):
            raise(NaaradClientException(tok[0]+" needs at least one parameter, got none"));

        id=int(tok[1]);
        for keys in settings5.gPacketHistory:
            if (isinstance(keys,tuple)):
                if (int(keys[0])==id):
                    paramList.append(keys[1]);
            else:
                if (int(keys) == id):
                    paramList.append(settings5.NAARAD_NAMELESS_PACKETS);
            
        # Convert the list to a list of unique elements
        paramList=list(set(paramList));
        paramStr='';
        for i in len(paramList):
            paramStr += paramList[i]+' ';
        print('paramList=',paramStr);
        pass;
    #
    #--------------------------------------------------------------------------
    #        
    def run(self):
        #global gCurrentPacket;
        #global gPacketHistory, gTimeStamp0Cache;

        print ("Starting " + self.name + ". Watching fd " + str(self.myc1.fileno()));

        finish = False;
        while (not finish):

            # First block via select.select waiting for someone to
            # call on the myc1 socket.  This should only get the read
            # fd, everything else is an error.
            try:
                rSockList = [self.myc1.fileno()];
                fdr,fdw,fde = select.select(rSockList,[],[]);
                for s in fde:
                    print ("select.select got exceptional fd.  Exiting.");
                    finish = True;
                    break;
                for s in fdw:
                    print ("select.select got writeable fd.  Strange...");
                    finish = True;
                    break;
            except RuntimeError as e:
                print ("ClientThread: RuntimeError during select().");
                break;

            # Having gotten a read fd from select.select() above, do a
            # non-blocking read (timeout of 5.0sec).  If timed out,
            # close the socket.  If receive() returns a message length
            # of zero, the client-side had a problem and socket might
            # be closed.  So then also shutdown the socket.
            #
            # This combination of blocking with select.select() and
            # then doing a non-blocking but with timeout read() should
            # ensure that (a) the thread does not loop idly, and (b)
            # if the client side dies or closes socket, this thread
            # also closes connection and exits.
            try:
                msg="";
                self.myc1.getSock().settimeout(5.0);#Timeout for 5s
                msg = self.myc1.receive();
                self.myc1.getSock().settimeout(None);#Set the sock back to blocking
            except socket.timeout as e:
                self.closeSock(self.myc1.getSock(),"Timed out.  Closing connection.");
                break;
            except socket.error as e:
                self.closeSock(self.myc1.getSock(), "ClientThread: SocketError during receive(). "+str(e));
                break;
            except RuntimeError as e:
                self.closeSock(self.myc1.getSock(), "ClientThread: RuntimeError during receive(). "+str(e));
                break;
            if (len(msg) == 0):
                self.closeSock(self.myc1.getSock(), "Possible EOF received from client.  Shutting down the connection");
                break;

            try:
                tok="";
                #print("M="+msg);
                if (len(msg) > 0):
                    #print "MSG: "+msg;
                    tok=msg.strip().split();
                if (len(tok) > 0):
                    cmd = tok[0].strip()
                    print (str(self.name)+" got: \""+msg+"\"");
                    if (cmd == "open"):
                        self.uno.open(); # Checks internally if it is already open
                    elif (cmd == "close"):
                        self.uno.close(); # Checks internally if it already closed
                    elif (cmd == "gett"):
                        print ("running cmd "+cmd+"@"+self.name);
                        data=self.pogo.gettemp();
                        print ("GETT: ",data);
                    #self.myc1.send(data.strip());
                    elif (cmd == "getnodelist"):
                        self.getNodeList(tok);
                    elif (cmd == "getparamlist"):
                        self.getParamList(tok);
                    elif (cmd == "gethpkt"):
                        try:
                            # if (len(tok) >= 2):
                            #     print "RSID="+tok[1]+" "+settings5.gCurrentPacket[int(tok[1])];
                            #keys  = settings5.gPacketHistory.keys();
                            key = int(tok[1]);
                            n = len(settings5.gPacketHistory[key]);
                            #n = min(n,10);
                            for i in range(n):
                                print ("key: ",key," ",settings5.gPacketHistory[key][i]);
                                self.myc1.send(settings5.gPacketHistory[key][i]);
                        except KeyError:
                            print ("gethpkt::Key ",tok[1]," not found");
                        self.myc1.send("PHINISHED }");
                        print ("PHINISHED");
                    elif (cmd == "getcpkt"):
                        try:
                            if (len(tok) >= 2):
                                print ("RSID="+tok[1]+" "+settings5.gCurrentPacket[int(tok[1])]);
                            self.myc1.send(settings5.gCurrentPacket[int(tok[1])]);
                        except KeyError:
                            print ("getcpkt::Key ",tok[1]," not found");
                            self.myc1.send("{\"rf_fail\":1 }");
                            #mm="{\"rf_fail\":1 }";
                            #self.myc1.send(mm.encode("UTF-8"));
                    elif (cmd == "get"):
                        print ("running cmd "+cmd+"@"+self.name);
                        data=self.pogo.getrtemp();
                        print ("Data = ",data);
                        self.myc1.send(data.strip());
                    elif (cmd == "cget"):
                        while(self.uno.inWaiting() > 0):
                            data=self.uno.readline();
                            self.myc1.send(data.strip());
                    elif (cmd == "tell"):
                        if (len(tok) >= 3):
                            self.pogo.tell(int(tok[1]),int(tok[2]));
                    elif (cmd == "pogocmd"):
                        val = self.pogo.sendCmd(cmd);
                    #print ("MCTh: pogocmd = ",val);
                        self.myc1.send(val.strip());
                    elif (cmd == "done"):
                    #self.uno.close();
                        self.closeSock(self.myc1.getSock(), "good bye");
                        break;
                    elif (cmd=="RFM_SEND"):
                        #self.uno.send(tok[0]+" "+tok[1]+" "+tok[2]);
                        if (len(tok) < 5):
                            raise(NaaradClientException("Usage: "+tok[0]+" CMD NODEID PORT TIMEOUT"));
                        self.uno.send(tok[0]+" "+tok[1]+" "+tok[2]+" "+tok[3]+" "+tok[4]);
                    elif (cmd=="notify"):
                        notifyForNodeID=int(tok[1]);
                        notifyForPktID=[int(tok[2]),str(tok[3])]; #[cmd,src]
                        if (len(tok)<5):
                            timeOut=None;
                        else:
                            timeOut = float(tok[4]);
                        notifyOnCond=Condition();

                        print ("Registerd: ",notifyForNodeID,notifyForPktID);
                        settings5.gClientList.register(notifyForNodeID, notifyOnCond, notifyForPktID);
                        with notifyOnCond:
                            notifyOnCond.wait(timeOut);
                            cpkt=settings5.gCurrentPacket[notifyForNodeID];
                            cpkt=Utils.addTimeStamp("tnot",cpkt);
                            self.myc1.send(cpkt);
                        settings5.gClientList.unregister(notifyOnCond);
                        break;
                        #print settings5.gClientList.getIDList(),settings5.gClientList.getCondList()
                    else:
                        print ("Command ",msg," not understood");
            except (RuntimeError):#, socket.error as e):
                print ("ClientThread: Error during cmd handling.")
                break;
            except NaaradClientException as e:
                print ("NaaradClientException: "+str(e));
                break;

        print ("Exiting " + self.name);
        #self.__del__();
