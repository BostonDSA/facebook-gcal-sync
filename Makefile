REPO      := boston-dsa/facebook-gcal-sync
STAGES    := lock zip plan
CLEANS    := $(foreach STAGE,$(STAGES),clean-$(STAGE))
PYTHON    := $(shell cat .python-version | cut -d'.' -f1,2)
RELEASE   := $(shell git describe --tags --always)
TIMESTAMP := $(shell date +%s)

.PHONY: default apply clean clobber $(STAGES) $(CLEANS)

default: zip
lock: Pipfile.lock
zip: lock dist/alarm.zip dist/sync.zip
plan: zip

.docker dist:
	mkdir -p $@

.docker/lock: Pipfile
.docker/zip: src
.docker/%: | .docker
	docker build \
	--build-arg PYTHON=$(PYTHON) \
	--build-arg AWS_ACCESS_KEY_ID \
	--build-arg AWS_DEFAULT_REGION \
	--build-arg AWS_SECRET_ACCESS_KEY \
	--build-arg TF_VAR_RELEASE=$(RELEASE) \
	--iidfile $@ \
	--tag $(REPO):$* \
	--tag $(REPO):$*-$(TIMESTAMP) \
	--target $* \
	.

.env:
	cp $@.example $@

Pipfile.lock: .docker/lock
	docker run --rm --entrypoint cat $$(cat $<) $@ > $@

dist/alarm.zip dist/sync.zip: dist/%: .docker/zip | dist
	docker run --rm --entrypoint cat $$(cat $<) $* > $@

apply: .docker/plan
	docker run --rm $$(cat $<)

clean: $(CLEANS)

clobber: clean
	docker image ls $(REPO) --quiet | xargs docker image rm --force
	rm -rf .docker dist

$(CLEANS): clean-%:
	docker image ls $(REPO):$*-* --format '{{.Repository}}:{{.Tag}}' | xargs docker image rm
	rm -rf .docker/$**

$(STAGES): %: .docker/%
