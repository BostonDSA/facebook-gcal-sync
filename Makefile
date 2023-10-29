REPO      := boston-dsa/facebook-gcal-sync
PYTHON    := $(shell cat .python-version | cut -d'.' -f1,2)

build:
	docker build \
		--file Dockerfile.build \
		--output type=local,dest=dist \
		--build-arg PYTHON=$(PYTHON) \
		--tag $(REPO):build \
		.
