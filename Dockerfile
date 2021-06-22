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
RUN mkdir dist
RUN pip install -r requirements-lock.txt -t .
RUN find . -name __pycache__ | xargs rm -rf
RUN zip -9r dist/sync.zip .
COPY src/alarm.py .
RUN zip -9r dist/alarm.zip alarm.py

FROM hashicorp/terraform:${TERRAFORM} AS plan
WORKDIR /var/task/
COPY *.tf /var/task/
ARG AWS_ACCESS_KEY_ID
ARG AWS_DEFAULT_REGION=us-east-1
ARG AWS_SECRET_ACCESS_KEY
ARG AWS_ROLE_ARN
RUN echo "${AWS_ACCESS_KEY_ID}"
RUN terraform init -backend-config="role_arn=${AWS_ROLE_ARN}" \
  -backend-config="access_key=${AWS_ACCESS_KEY_ID}" \
  -backend-config="secret_key=${AWS_SECRET_ACCESS_KEY}"
RUN terraform fmt -check
COPY --from=zip /var/task/dist/ /var/task/dist/
ARG TF_VAR_VERSION
RUN terraform plan -var="AWS_ROLE_ARN=${AWS_ROLE_ARN}" -out terraform.zip
CMD ["apply", "terraform.zip"]
