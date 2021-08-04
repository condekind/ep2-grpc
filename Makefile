# =========================================================================== #

srcdir = ./src
gendir = ./src/gen
genobj = $(gendir)/*.py


# --------------------------------------------------------------------------- #

# Ensures `gen` rule runs if a $genobj is needed
$(genobj): gen;


run_serv_arm: $(genobj)
	./run svc_arm $(arg)

run_cli_arm: $(genobj)
	./run cln_arm $(arg)

run_serv_comp: $(genobj)
	./run svc_comp $(arg1) $(arg2) $(arg3)

run_cli_comp: $(genobj)
	./run cln_comp $(arg)


# Silently creates empty __init__.py files to enable python imports
gen:
	@touch $(srcdir)/__init__.py
	@touch $(gendir)/__init__.py
	$(info Generating gRPC files...)
	@./run gen

# Removes generated files and silently removes python ugly import workarounds
clean:
	-@rm $(srcdir)/__init__.py $(gendir)/__init__.py 2>/dev/null || true
	rm -rf $(genobj)


# =========================================================================== #