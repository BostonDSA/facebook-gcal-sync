.PHONY: default apply clean plan

default: plan

.terraform:
	terraform init

credentials.json:
	$(error Need credentials.json for Google Cloud access)

terraform.tfvars:
	cp $@.example $@

clean:
	rm -rf .terraform

apply plan: credentials.json terraform.tfvars | .terraform
	terraform $@
