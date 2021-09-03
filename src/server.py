# =========================================================================== #
from typing import Optional, Any, List, Tuple, Dict, TextIO

from concurrent import futures
import logging, sys
import grpc

from proto import msg_pb2
from proto import msg_pb2_grpc

## TODO: Get type hinting from betterproto to work
# try:
#     import betterproto
# except:
#     from proto import msg_pb2
#     from proto import msg_pb2_grpc
# else:
#     from proto import msg as msg_pb2
#     from proto import msg_pb2_grpc


# --------------------------------------------------------------------------- #

class NoobDB(msg_pb2_grpc.RemoteQueryServicer):

    # Initializes structures, sets options, etc.
    def __init__(self, debugOutputFile: TextIO = sys.stderr) -> None:
        super().__init__()
        self.debugOutputFile = debugOutputFile
        self.db: Dict[int, msg_pb2.Val]  = {}


    # Tries to insert contents from `request` into self.db
    def insert(self, request: msg_pb2.InsertReq,
                     context: grpc.ServicerContext) -> msg_pb2.InsertAns:
        print(f'key={request.key}', end=' ', file=self.debugOutputFile)
        if request.key in self.db:
            print('already present in the database', file=self.debugOutputFile)
            return msg_pb2.InsertAns(errNo=msg_pb2.KEY_ALREADY_PRESENT)
        else:
            self.db[request.key] = request.val
            print(f'was inserted in the database with val={request.val}',
                  file=self.debugOutputFile)
            return msg_pb2.InsertAns()


    def query(self, request: msg_pb2.QueryReq, context: grpc.ServicerContext) -> msg_pb2.QueryAns:
        return msg_pb2.QueryAns(val=msg_pb2.Val(data=42, desc='towels'))


    def shutdown(self, request: msg_pb2.ShutdownReq, context: grpc.ServicerContext) -> msg_pb2.ShutdownAns:
        return msg_pb2.ShutdownAns(status=True)


# --------------------------------------------------------------------------- #

# Manages a single server and holds an instance of the offered service (db)
class ServerManager:

    # Initializes structures, sets options, etc.
    def __init__(self,  opts: Optional[List[Tuple[str, Any]]] = None,
                        port: str = '50051',
                        max_workers: int = 10) -> None:

        # Init server
        self.server = grpc.server(
                futures.ThreadPoolExecutor(max_workers=max_workers),
                options=opts)

        # Init our key-val DB
        self.db = NoobDB()

        # Registers our servicer (db) to the server managed by this object
        msg_pb2_grpc.add_RemoteQueryServicer_to_server(self.db, self.server)
        self.server.add_insecure_port(f'[::]:{port}')


    # Starts the initialized server
    def serve(self, timeout: float = 2.0):
        logging.basicConfig()
        self.server.start()
        self.server.wait_for_termination(timeout=timeout)


# --------------------------------------------------------------------------- #

def run_server(port: str = '50051'):
    serverOpts = [
        ('grpc.client_idle_timeout_ms',      5000),
        ('grpc.keepalive_timeout_ms',        5000),
        ('grpc.server_handshake_timeout_ms', 4000),
        ('grpc.grpclb_call_timeout_ms',      4000),
        ('grpc.dns_ares_query_timeout',      4000),
    ]

    sm = ServerManager(opts=serverOpts, port=port)

    sm.serve(timeout=2.0)


# =========================================================================== #