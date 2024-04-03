# TODO: Make these Makefile variables shared across project
PROJECT := $(shell gcloud config get-value project)
REPOSITORY := gallery
REGION := us-central1
PREFIX := $(REGION)-docker.pkg.dev/$(PROJECT)/$(REPOSITORY)
TAG := latest

.PHONY: build-images
build-images:
	docker build -t $(PREFIX)/publisher:$(TAG) src/publisher
	docker build -t $(PREFIX)/scanner:$(TAG) src/scanner
	docker build -t $(PREFIX)/parser:$(TAG) src/parser

.PHONY: push-images
push-images:
	docker push $(PREFIX)/publisher:$(TAG)
	docker push $(PREFIX)/scanner:$(TAG)
	docker push $(PREFIX)/parser:$(TAG)

.PHONY: run-parser
build-and-run-parser:
	docker build -t gallery-parser:local src/parser
	docker run --rm -it \
		-p 8000:8080 \
		-e "MONGO_URI=$(MONGO_URI)" \
		-e "PORT=8080" \
		-e "TIMEOUT=600" \
		gallery-parser:local
