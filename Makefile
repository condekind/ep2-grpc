# =========================================================================== #

srcdir = ./src
gendir = ./proto
genobj = $(gendir)/msg_pb2.py $(gendir)/msg_pb2_grpc.py


# --------------------------------------------------------------------------- #

demo: $(genobj)
ifeq (, $(shell command -v tmux))
# tmux not found: running demo with each host in a background job
	@python3 run svc_arm arg=50052 &
	@python3 run svc_arm arg=50053 &
	@python3 run svc_comp arg1=50051 arg2=localhost:50052 arg3=localhost:50053 &
	@sleep 1.618 && python3 run cln_comp arg=localhost:50051 < misc/client_512.txt
else
# tmux found: running demo with a session for each *server*
	@tmux kill-session -t svc_arm_session  2>/dev/null || true
	@tmux kill-session -t svc_arm_session  2>/dev/null || true
	@tmux kill-session -t svc_comp_session 2>/dev/null || true
	@command tmux new-session -d -s svc_siga_session 'python3 run svc_arm arg=50052'
	@command tmux new-session -d -s svc_matr_session 'python3 run svc_arm arg=50053'
	@command tmux new-session -d -s svc_comp_session 'python3 run svc_comp arg1=50051 arg2=localhost:50052 arg3=localhost:50053'
	@sleep 1.618 && python3 run cln_comp arg=localhost:50051 < misc/client_512.txt
endif

run_serv_arm: $(genobj)
	@python3 run svc_arm $(arg)

run_cli_arm: $(genobj)
	@python3 run cln_arm $(arg)

run_serv_comp: $(genobj)
	@python3 run svc_comp $(arg1) $(arg2) $(arg3)

run_cli_comp: $(genobj)
	@python3 run cln_comp $(arg)

# Protobuf compilation (generate gRPC files)
$(genobj):
	@python3 run compile_proto 2>/dev/null

# Removes generated files
clean:
	rm -rf $(genobj)
	rm -rf ./__pycache__
	rm -rf ./*/__pycache__
	rm -rf ./*/*/__pycache__


# =========================================================================== #