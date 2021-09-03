# =========================================================================== #
from enum import Enum
from typing import Optional, Any, List, Tuple, Dict, TextIO
import logging, sys

import grpc
from proto import msg_pb2
from proto import msg_pb2_grpc

# --------------------------------------------------------------------------- #

class ClientApp:

    def __init__(self, debugOutputFile: TextIO = sys.stderr) -> None:
        self.debugOutputFile = debugOutputFile


    def run(self):
        with grpc.insecure_channel('localhost:50051') as channel:
            stub     = msg_pb2_grpc.RemoteQueryStub(channel)
            val      = msg_pb2.Val(data=1729, desc='YOLO')
            response = stub.insert(msg_pb2.InsertReq(key=1337, val=val))
        print(f'Insertion {"successful" if (response.errNo == msg_pb2.OK) else "failed"}!')


# --------------------------------------------------------------------------- #


def run_client():
    logging.basicConfig()
    client = ClientApp()
    client.run()

# =========================================================================== #