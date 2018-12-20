# Boston DSA Facebook Event Sync

Sync [facbook.com/BostonDSA](https://facebook.com/BostonDSA/events) facebook events to Google Calendar.

This app runs on AWS [Lambda](https://aws.amazon.com/lambda/) with an hourly trigger in [CloudWatch](https://aws.amazon.com/cloudwatch) events.

## How it Works

Using a [facebook page token](https://developers.facebook.com/docs/pages/access-tokens), a client to facebook's [Graph API](https://github.com/mobolic/facebook-sdk) requests upcoming events from the Boston DSA facebook page using the `/BostonDSA/events` REST API endpoint.

A hash is taken of each event returned by the request to compare to a private extended property in Google Calendar.

Next, using a [Google Service Account](https://cloud.google.com/iam/docs/understanding-service-accounts), a client to Google's [Calendar API](https://developers.google.com/calendar/v3/reference/) requests events in the same window as above using the `/v3/calendars/<calendarId>/events` REST API endpoint. Events are filtered by a private extended property that indicates the event's origin is the the facebook page, `BostonDSA`.

Events that appear in the request to Graph API, but not the request to Google are created. Events that are found in both requests, but have different hashes are updated in Google. Events that are returned by Google, but can no longer be found on facebook are deleted.

## Deployment

The access keys for facebook and Google are encrypted and stored in AWS [SecretsManager](https://aws.amazon.com/secrets-manager/). The IAM role assumed by the Lambda is granted permission to decrypt and access these keys so that they don't need to be shared between collaborators on the project.

### Packaging

Before the project can be deployed it will need to be packaged as a zip file to upload to Lambda.

Use `docker-compose` to generate an artifact:

```bash
docker-compose run --rm package
docker-compose down
```

This will build a `package.zip` file in the `dist` directory of the repo, which is ignored by git.

### Deploying

This app is deployed using [terraform](https://terraform.io).

You will need AWS access keys with permission to access IAM, CloudWatch, Lambda, and SecretsManager resources.

It's recommended that you store your keys in [configuration and credential](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html) files. This allows you to reference the keys by profile name and reduces the chances of accidentally exposing keys.

Copy the `terraform.tfvars.example` file to `terraform.tfvars` and fill in with the correct values.

Initialize the terraform project:

```bash
terraform init
```

View any potential configuration changes:

```bash
terraform plan
```

Apply any configuration changes:

```bash
terraform apply
```
