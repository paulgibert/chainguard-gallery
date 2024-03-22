# TODO: Make these Makefile variables shared across project
PROJECT := $(shell gcloud config get-value project)
REPOSITORY := gallery
REGION := us-central1
PREFIX := $(REGION)-docker.pkg.dev/$(PROJECT)/$(REPOSITORY)
TAG := latest

.PHONY: build-images
build-images:
	docker build -t $(PREFIX)/publisher:$(TAG) src/publisher
	docker build -t$(PREFIX)/scanner:$(TAG) src/scanner

.PHONY: push-images
push-images:
	docker push $(PREFIX)/publisher:$(TAG)
	docker push $(PREFIX)/scanner:$(TAG)
