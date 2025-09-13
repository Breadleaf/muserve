SHELL:=$(shell which bash)

all: help

help:
	@echo "make targets:"
	@echo "    setup(selfsign)"
	@echo "    selfsign"
	@echo "    clean"

setup: selfsign 

selfsign:
	mkdir -p certs
	openssl genpkey -algorithm RSA -out ./certs/server.key
	openssl req -new -key ./certs/server.key -out ./certs/server.csr
	openssl x509 -req -in ./certs/server.csr -signkey ./certs/server.key -out ./certs/server.crt

clean:
	rm -rf ./certs | true
