
## How it works

TBD

## Development

### Prerequisites

* Python
* pip
* pipenv
* docker (for running build deploy locally)

## Set up locally

1. Copy .env.example to .env.
1. Populate secrets.
1. `pipenv sync --dev` to install Python depenencies.
1. `pipenv shell` to load virtual env.
1. `python3 src/sync.py` to do a dry run (add the `-s` flag to push to airtable).


## Deployment

This repo is configured to [deploy automatically](./.travis.yml) on tagged releases, but manual deployment is also possible.

First, set up your `.env` file with make and fill in at least your AWS credentials

```bash
make .env
```

Build the Lambda deployment packages (requires Docker)

```bash
make
```

Generate plan for updating infrastructure

```bash
make plan
```

Apply changes

```bash
make apply
```
