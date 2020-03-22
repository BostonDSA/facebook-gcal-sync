ARG PYTHON=3.8
ARG TERRAFORM=latest

FROM lambci/lambda:build-python${PYTHON} AS lock
RUN pipenv lock 2>&1
COPY Pipfile* /var/task/
RUN pipenv lock -r > requirements-lock.txt
RUN pipenv lock -r -d > requirements-dev-lock.txt

FROM lambci/lambda:build-python${PYTHON} AS zip
COPY src/sync.py .
COPY --from=lock /var/task/ .
RUN pip install -r requirements-lock.txt -t .
RUN find . -name __pycache__ | xargs rm -rf
RUN zip -9r sync.zip .
COPY src/alarm.py .
RUN zip -9r alarm.zip alarm.py

FROM hashicorp/terraform:${TERRAFORM} AS plan
WORKDIR /var/task/
COPY *.tf /var/task/
ARG AWS_ACCESS_KEY_ID
ARG AWS_DEFAULT_REGION=us-east-1
ARG AWS_SECRET_ACCESS_KEY
RUN terraform init
RUN terraform fmt -check
COPY --from=zip /var/task/*.zip /var/task/dist/
ARG TF_VAR_RELEASE
RUN terraform plan -out terraform.zip
CMD ["apply", "terraform.zip"]
