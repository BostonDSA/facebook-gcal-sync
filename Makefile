PWD		  := $(shell pwd)
PYTHON    := $(shell cat .python-version | cut -d'.' -f1,2)
REPO      := boston-dsa/facebook-gcal-sync
TERRAFORM := latest
VERSION   := manual

env:
	cp .env.example .env

build:
	docker build \
		--output type=local,dest=dist \
		--build-arg PYTHON=$(PYTHON) \
		--tag $(REPO):build \
		.

stage: terraform-init terraform-lint terraform-plan

deploy: terraform-apply

terraform-init:
	docker run --rm -i -t -w /var/task \
		-v $(PWD):/var/task \
		--env-file .env \
		hashicorp/terraform:$(TERRAFORM) init

terraform-lint:
	docker run --rm -i -t -w /var/task \
		-v $(PWD):/var/task \
		--env-file .env \
		hashicorp/terraform:$(TERRAFORM) fmt -check

terraform-plan:
	docker run --rm -i -t -w /var/task \
		-v $(PWD):/var/task \
		--env-file .env \
		hashicorp/terraform:$(TERRAFORM) plan -var AWS_ROLE_ARN=$$AWS_ROLE_ARN -var VERSION=$(VERSION) -out tfplan

terraform-apply:
	docker run --rm -i -t -w /var/task \
		-v $(PWD):/var/task \
		--env-file .env \
		hashicorp/terraform:$(TERRAFORM) apply tfplan
