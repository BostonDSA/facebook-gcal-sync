FUNCTIONS := alarm sync
REPO      := boston-dsa/facebook-gcal-sync
STAGES    := lock zip plan
PACKAGES  := $(foreach FUNC,$(FUNCTIONS),dist/$(FUNC).zip)
PYTHON    := $(shell cat .python-version | cut -d'.' -f1,2)
VERSION   := $(shell git describe --tags --always)

.PHONY: default apply clean clear clobber $(STAGES)

default: Pipfile.lock $(PACKAGES)

.docker dist:
	mkdir -p $@

.docker/lock: Dockerfile Pipfile
.docker/zip: .docker/lock $(shell find src -type f)
.docker/plan: .docker/zip
.docker/%: | .docker
	docker build \
	--build-arg PYTHON=$(PYTHON) \
	--build-arg AWS_ACCESS_KEY_ID \
	--build-arg AWS_DEFAULT_REGION \
	--build-arg AWS_SECRET_ACCESS_KEY \
	--build-arg AWS_ROLE_ARN \
	--build-arg TF_VAR_VERSION=$(VERSION) \
	--iidfile $@ \
	--tag $(REPO):$* \
	--target $* \
	.

.env:
	cp $@.example $@

Pipfile.lock: .docker/lock
	docker run --rm --entrypoint cat $$(cat $<) $@ > $@

apply: .docker/plan
	docker run --rm \
	--env AWS_ACCESS_KEY_ID \
	--env AWS_DEFAULT_REGION \
	--env AWS_SECRET_ACCESS_KEY \
	--env AWS_ROLE_ARN \
	$$(cat $<)

clean:
	rm -rf .docker

clobber: clean
	docker image ls $(REPO) --quiet | uniq | xargs docker image rm --force
	rm -rf dist

$(PACKAGES): .docker/zip dist
	docker run --rm --entrypoint cat $$(cat $<) $@ > $@

$(STAGES): %: .docker/%
