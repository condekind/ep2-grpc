# =========================================================================== #
from dataclasses import dataclass
from enum import Enum


from src.gen import msg_pb2
from src.gen import msg_pb2_grpc

# --------------------------------------------------------------------------- #

Key  = int
Desc = str
Val  = int


class InsertStatus(Enum):
    SUCCESS    =  0
    KEY_IN_USE = -1


@dataclass(frozen=True)
class QueryResult:
    desc: Desc
    val:  Val


class NoobServer():

    @staticmethod
    def Query_NotFound() -> QueryResult:
        return QueryResult('', 0)

    def insert(self, key: Key, desc: Desc, val: Val) -> InsertStatus:
        return InsertStatus.KEY_IN_USE

    def query(self, key: Key) -> QueryResult :
        return NoobServer.Query_NotFound()

    def shutdown(self) -> None:
        return

    def sayHello(self) -> None:
        print('Hello')


# =========================================================================== #