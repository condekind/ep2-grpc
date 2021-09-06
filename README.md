
# EP2 - gRPC assignment

## Before you start...

### Dependencies
#### Required

- GNU Make or compatible alternative
- Python 3.8^
- [grpcio](https://pypi.org/project/grpcio/), [grpcio-tools](https://pypi.org/project/grpcio-tools/)

#### Optional

- [mypy-protobuf](https://github.com/dropbox/mypy-protobuf#installation)
- tmux
- nltk (test input generation, mostly just for the ready-to-use data)

The client and server should run without any extras, as required by the spec. However, having [Poetry](https://python-poetry.org/docs/master/) will let you quickly setup a virtualenv, which might be desirable.

```bash
# For poetry, this should suffice
poetry install
poetry shell
```

If you have problems with the required Python version to run the project, I strongly recommend using [pyenv](https://github.com/pyenv/pyenv#simple-python-version-management-pyenv).

Finally, all the instructions target a local environment. The arguments may be changed to remote ```address``` or ```address:port``` values (at your own risk).

## Part 0

Both the client and server use a "demux" script called ```run```, purposely left non-executable. It will be passed to Python by ```make```, so *make* sure you don't try running it directly. Or don't, but it's a good idea to inspect it anyway. This "demuxing" effect could take place in the ```Makefile``` itself, however, ```make``` syntax sucks and I was using ```run``` to quickly debug the early versions of the project. In the end I just didn't feel like moving the entire logic back to the ```Makefile```. This also meant I had more flexibility between the Makefile and the main programs, so I ended only needing one ```server.py``` and one ```client.py```.

## Part 1

To start the server:
```bash
make run_svc_arm arg=50051
```

To start the client:
```bash
make run_cln_arm arg=localhost:50051
```

On the client, you can pass commands in the following format:

> I,ch,um string de descrição,val - insere no servidor a chave ch, associada ao string e ao valor val, escreve na saída padrão o valor de retorno do procedimento (0 ou -1);
>
> C,ch - consulta o servidor pelo conteúdo associado à chave ch e escreve na saída o string e o valor, separados por uma vírgula, ou apenas -1, caso a chave não seja encontrada;
>
> T - termina a operação do servidor, envia zero como valor de retorno e termina.

Some testing input (```misc/input.txt```) was generated using ```misc/gen_input.py```. If you wish to try it, run:

```bash
# Server: from one terminal/session, run:
make run_svc_arm arg=50051
# Client: from another, run:
make run_cli_arm arg=50051 < misc/input.txt
```

Alternatively, the same result is obtained by just running the scripts:

```bash
# Server: from one terminal/session, run:
./server
# Client: from another, run:
./client
```

## Part 2

To start the forwarding (main) server:
```bash
make run_serv_comp arg1=50051 arg2=localhost:50052 arg3=localhost:50053
```

To start the client, you'd run the code below. **But** without starting the auxiliary servers, you'll get boring results/errors.

```diff
< make run_cli_comp arg=localhost:50051
```

Auxiliary servers (these are the same used in the first step):
```bash
make run_serv_arm arg=localhost:50052
make run_serv_arm arg=localhost:50053
```

Now the client is good to go:

```bash
make run_cli_comp arg=localhost:50051
```

Supported client commands:

> C,ch - consulta o servidor pelo conteúdo associado à chave ch e escreve na saída os valores de nome, matr, curso e cred,separados por vírgulas, ou apenas -1, caso a chave não seja encontrada;
>
> T - termina a operação do servidor, envia zero como valor de retorno e termina.

More testing input (```misc/client_XXXX.txt```) was generated with the same script. As with part-1, there are shorcuts to save some up-arrow strokes and copy pasting:

```bash
# Start all the servers, wait φ seconds and start the client with misc/client_512.txt as input
make
```

Or:

```bash
# Main server on port 50051, querying from localhost:50052 and localhost:50053
./server comp
# Client with misc/client_$1.txt as input
./client 512  # or one of the other values found in misc/client_XXXX.txt
```

* remember to start the auxiliary servers yourself, or change the script ```server``` to query your own servers


In regards to the generated input, there are two fake db files: ```misc/siga.json``` and ```misc/matr.json``` (with .txt versions for inspection, if needed). They're only loaded when the auxiliary servers are served locally with the default ports (50052 and 50053).

If you want to see how they were generated, ```misc/gen_input.py``` was originally a notebook, now converted to script. You'll need nltk and the collections "machado" (part-1) and "names" (part-2). If you download *only* these from the GUI, you'll get an error from the RegexParser about punkt, or some other dependency. You could download what's needed, but I recommend going to the first tab and downloading "tutorial"-like collections, which should include the needed internals (e.g. the one called ```book```).