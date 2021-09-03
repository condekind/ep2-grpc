# =========================================================================== #

srcdir = ./src
gendir = ./proto
genobj = $(gendir)/*_pb2*.py


# --------------------------------------------------------------------------- #

# Ensures `compile_proto` rule runs if a $genobj is needed
$(genobj): compile_proto;

run_serv_arm: $(genobj)
	./run svc_arm $(arg)

run_cli_arm: $(genobj)
	./run cln_arm $(arg)

run_serv_comp: $(genobj)
	./run svc_comp $(arg1) $(arg2) $(arg3)

run_cli_comp: $(genobj)
	./run cln_comp $(arg)

run: FORCE
	./run server &
	./run client

FORCE:

# Generates _pb2 and _pb2_grpc files
compile_proto:
	$(info Generating gRPC files...)
	@./run compile_proto

# Removes generated files and silently removes python ugly import workarounds
clean:
	rm -rf $(genobj)
	rm -rf ./__pycache__
	rm -rf ./*/__pycache__
	rm -rf ./*/*/__pycache__
	rm -rf ./proto/msg.py


# =========================================================================== #