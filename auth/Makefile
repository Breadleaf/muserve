SHELL:=$(shell which bash)

all: help

help:
	@echo "make targets:"
	@echo "    setup(venv)"
	#@echo "    setup(venv, selfsign)"
	#@echo "    selfsign"
	@echo "    venv"
	@echo "    clean"

setup: venv #selfsign 

#selfsign:
#	openssl genpkey -algorithm RSA -out server.key
#	openssl req -new -key server.key -out server.csr
#	openssl x509 -req -in server.csr -signkey server.key -out server.crt

venv:
	python3 -m venv venv
	source venv/bin/activate && pip install -r requirements.txt

clean:
	#rm server.crt | true
	#rm server.csr | true
	#rm server.key | true
	rm -rf venv | true
	rm -rf __pycache__ | true
