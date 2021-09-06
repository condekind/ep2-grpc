# =========================================================================== #

import sys, datetime, threading, json
from typing import Dict
from logging import debug, basicConfig, Formatter, DEBUG
from concurrent import futures

import grpc
from proto import msg_pb2 as msg
from proto.msg_pb2_grpc import (
    RemoteQueryServicer, RemoteQueryStub, FwdQueryServicer,
    add_RemoteQueryServicer_to_server, add_FwdQueryServicer_to_server)

# --------------------------------------------------------------------------- #

_stdOpts = [
    ('grpc.client_idle_timeout_ms',      5000),
    ('grpc.keepalive_timeout_ms',        5000),
    ('grpc.server_handshake_timeout_ms', 4000),
    ('grpc.grpclb_call_timeout_ms',      4000),
    ('grpc.dns_ares_query_timeout',      4000),
]
_relTime = False
_timeFmt = '%(relativeCreated)6d' if _relTime else '%(asctime)s'
_logFmt = f'{_timeFmt}[%(thread)d]%(threadName)s: %(message)s'

Formatter.formatTime = (
    lambda self, record, datefmt: datetime.datetime.fromtimestamp(
            record.created, datetime.timezone.utc).astimezone().isoformat())


# --------------------------------------------------------------------------- #

# Part 1 servicer class
class KeyValServicer(RemoteQueryServicer):

    # Initializes structures, sets options, etc.
    def __init__(self, db, dbLock, shutdownEv):
        super().__init__()
        self._db         = db
        self._dbLock     = dbLock
        self._shutdownEv = shutdownEv
        self._available  = True


    # ------------ RemoteQuery methods offered by the Server/arm ------------ #

    # Idea: substitute this simple "all-blocking Lock" by a Read-Write Lock:
    # https://www.oreilly.com/library/view/python-cookbook/0596001673/ch06s04.html
    def insert(self, req, _) -> msg.InsertAns:
        """Inserts the requested key:val in the DB if they're not present."""
        with self._dbLock:
            if not self._available:
                return msg.InsertAns(errNo=msg.SERVER_SHUTDOWN)
            elif req.key in self._db:
                debug(f'{req.key=}->already present in the database')
                return msg.InsertAns(errNo=msg.KEY_ALREADY_PRESENT)
            else:
                self._db[req.key] = req.val
                debug(f'{req.key=}->inserted:{req.val.desc=},{req.val.data=}')
                return msg.InsertAns()


    def query(self, req, _) -> msg.QueryAns:
        """Checks if the requested key is in the DB and replies accordingly."""
        with self._dbLock:
            if not self._available:
                return msg.QueryAns(errNo=msg.SERVER_SHUTDOWN)
            elif req.key in self._db:
                ans = self._db[req.key]
                debug(f'{req.key=}->found:{ans.desc=},{ans.data=}')
                return msg.QueryAns(val=ans)
            else:
                debug(f'{req.key=}->not found!')
                return msg.QueryAns(errNo=msg.KEY_NOT_FOUND)


    def shutdown(self, *_) -> msg.ShutdownAns:
        """Clears allocated resources and terminates, returing 0 on success."""
        debug(f'Received termination request. Shutting down...')
        with self._dbLock:
            self._available = False
            self._db.clear()
            self._shutdownEv.set()
        return msg.ShutdownAns(status=True)


# --------------------------------------------------------------------------- #

# Part 2 servicer class
class ForwardingServicer(FwdQueryServicer):

    # Initializes structures, sets options, etc.
    def __init__(self, shutdownEv, addrSiga, portSiga, addrMatr, portMatr):
        super().__init__()
        self._addrSiga, self._portSiga = addrSiga, portSiga
        self._addrMatr, self._portMatr = addrMatr, portMatr
        self._shutdownEv = shutdownEv
        self._available  = True


    # Idea: avoid the repeated __enter__ and __exit__ from the channels by
    # having a ref to it and mannually checking their state on the workers
    #self._sigaCh = grpc.insecure_channel(f'{self._addrSiga}:{self._portSiga}')
    #self._matrCh = grpc.insecure_channel(f'{self._addrMatr}:{self._portMatr}')
    def requestFromSiga(self, key) -> msg.QueryAns:
        with grpc.insecure_channel(f'{self._addrSiga}:{self._portSiga}') as ch:
            return RemoteQueryStub(ch).query(msg.QueryReq(key=key))
    def requestFromMatr(self, key) -> msg.QueryAns:
        with grpc.insecure_channel(f'{self._addrMatr}:{self._portMatr}') as ch:
            return RemoteQueryStub(ch).query(msg.QueryReq(key=key))


    # ------------- FwdQuery methods offered by the Server/comp ------------- #

    def queryAll(self, req, _) -> msg.QueryAllAns:
        """Queries two servers to return all info available on the requested key"""
        debug(f'Received query for {req.key=}')
        if not self._available:
            return msg.QueryAllAns(errNo=msg.SERVER_SHUTDOWN)

        sigaAns = self.requestFromSiga(req.key)
        if sigaAns.errNo:  # Key not found in the Siga server
            return msg.QueryAllAns(errNo=msg.KEY_NOT_FOUND,
                                   siga=msg.Val(data=0, desc=''),
                                   matr=msg.Val(data=0, desc=''))
        nome, matr = sigaAns.val.desc, sigaAns.val.data
        debug(f'First response: {nome=}, {matr=}')

        matrAns = self.requestFromMatr(matr)
        if matrAns.errNo:  # Key not found in the Matr server
            return msg.QueryAllAns(errNo=msg.EXT_NOT_FOUND,
                                   siga=msg.Val(data=matr, desc=nome),
                                   matr=msg.Val(data=0, desc='N/M'))
        curso, cred = matrAns.val.desc, matrAns.val.data
        debug(f'Second response: {curso=}, {cred=}')

        # Desired result, with all the information on the requested key
        return msg.QueryAllAns(siga=msg.Val(data=matr, desc=nome),
                               matr=msg.Val(data=cred, desc=curso))


    def shutdown(self, *_) -> msg.ShutdownAns:
        debug(f'Received termination request. Shutting down...')
        self._available = False
        with grpc.insecure_channel(f'{self._addrSiga}:{self._portSiga}') as ch:
            RemoteQueryStub(ch).shutdown(msg.ShutdownReq())
        with grpc.insecure_channel(f'{self._addrMatr}:{self._portMatr}') as ch:
            RemoteQueryStub(ch).shutdown(msg.ShutdownReq())
        self._shutdownEv.set()
        return msg.ShutdownAns(status=True)


# ----------------------------------- Wrapper ------------------------------- #

# Manages a single server and holds an instance of the offered servicer
class ServerManager:

    # For testing/demo only - in a regular run, {} is returned
    def _loadDB(self) -> Dict[int, msg.Val]:
        if self._port == '50052':
            with open('misc/siga.json', 'r') as sigaJson:
                return {  int(k): msg.Val(desc=v[0], data=int(v[1]))
                        for k,v in json.load(sigaJson).items()}
        elif self._port == '50053':
            with open('misc/matr.json', 'r') as matrJson:
                return {  int(k): msg.Val(desc=v[0], data=int(v[1]))
                        for k,v in json.load(matrJson).items()}
        else: return {}


    # Initializes structures, sets options, etc.
    def __init__(self, mode, port = '50051', max_workers = 8,
                 addrSiga = 'localhost', portSiga = '50052',
                 addrMatr = 'localhost', portMatr = '50053') -> None:
        self._port       = port
        self._workerPool = futures.ThreadPoolExecutor(max_workers=max_workers)
        self._shutdownEv = threading.Event()
        self._server     = grpc.server(self._workerPool, options=_stdOpts)
        basicConfig(format=_logFmt, level=DEBUG)

        # Part1-exclusive code
        if mode == 'svc_arm':
            self._db         = self._loadDB()
            self._dbLock     = threading.Lock()
            self._dbServicer = KeyValServicer(self._db, self._dbLock,
                                              self._shutdownEv)
            add_RemoteQueryServicer_to_server(self._dbServicer, self._server)

        # Part2-exclusive code
        elif mode == 'svc_comp':
            self._fwdServicer = ForwardingServicer(self._shutdownEv,
                                                    addrSiga, portSiga,
                                                    addrMatr, portMatr)
            add_FwdQueryServicer_to_server(self._fwdServicer, self._server)

        else: sys.exit(f'{mode=} is invalid!')


    # Starts the initialized server
    def serve(self):
        self._server.add_insecure_port(f'[::]:{self._port}')
        self._server.start()
        self._shutdownEv.wait()
        self._server.stop(grace=1.0)


# =========================================================================== #