# =========================================================================== #

from logging import debug, basicConfig, Formatter, DEBUG
import sys, datetime

import grpc
from proto import msg_pb2 as msg
from proto.msg_pb2_grpc import FwdQueryStub, RemoteQueryStub


# --------------------------------------------------------------------------- #

_relTime    = False
_timeFmt    = '%(relativeCreated)6d' if _relTime else '%(asctime)s'
_logFmt     = f'{_timeFmt}: %(message)s'
Formatter.formatTime = (
lambda self, record, datefmt: datetime.datetime.fromtimestamp(
    record.created,
    datetime.timezone.utc
).astimezone().isoformat())


# --------------------------------------------------------------------------- #

class ClientApp:

    def queryArm(self, stub) -> None:
        for line in (l.split(sep=',') for l in sys.stdin):

            if (op := line[0]) == 'I':
                val = msg.Val(data=int(line[3]), desc=line[2])
                req = msg.InsertReq(key=int(line[1]), val=val)
                ans = stub.insert(req)
                print(f'{-1 if ans.errNo else 0}')

            elif op == 'C':
                req = msg.QueryReq(key=int(line[1]))
                ans = stub.query(req)
                print(f'''{-1 if ans.errNo else
                        f"{ans.val.desc},{ans.val.data}"}''')

            elif op.strip() == 'T':
                stub.shutdown(msg.ShutdownReq())
                return

            else: debug(f'{op=} is not a valid operation!')


    def queryComp(self, stub) -> None:
        for line in (l.split(sep=',') for l in sys.stdin):

            if (op := line[0]) == 'C':
                req = msg.QueryReq(key=int(line[1]))
                ans = stub.queryAll(req)
                print('-1' if ans.errNo == msg.KEY_NOT_FOUND
                       else f'{ans.siga.desc},{ans.siga.data},'  # nome, matr
                          + f'{ans.matr.desc},{ans.matr.data}')  # curso, cred

            elif op.strip() == 'T':
                stub.shutdown(msg.ShutdownReq())
                return

            else: debug(f'{op=} is not a valid operation!')


    def __init__(self, mode) -> None:
        self._mode = mode
        basicConfig(format=_logFmt, level=DEBUG)


    def run(self, ip = 'localhost', port = 50051):
        with grpc.insecure_channel(f'{ip}:{port}') as ch:
            if self._mode == 'cln_arm': self.queryArm(RemoteQueryStub(ch))
            elif self._mode == 'cln_comp': self.queryComp(FwdQueryStub(ch))
            else: sys.exit(f'{self._mode=} is invalid!')


# =========================================================================== #