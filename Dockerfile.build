ARG PYTHON=3.11
FROM amazon/aws-lambda-python:${PYTHON} AS build

COPY Pipfile* .
COPY src .
COPY src/alarm.py .

# Install linux packages
RUN yum install -y git zip

# Install python packages
RUN pip install pipenv
RUN pipenv requirements > requirements-lock.txt
RUN pip install -r requirements-lock.txt -t .

# Clean-up
RUN find . -name __pycache__ | xargs rm -rf

# Package
RUN mkdir dist
RUN zip -9r dist/sync.zip .
RUN zip -9r dist/alarm.zip alarm.py

# Exports just the artifacts
FROM scratch AS output
COPY --from=build /var/task/dist /