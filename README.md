# Boston DSA Facebook Event Sync

Sync [facbook.com/BostonDSA](https://facebook.com/BostonDSA/events) facebook events to Google Calendar.

This app runs on AWS [Lambda](https://aws.amazon.com/lambda/) with an hourly trigger in [CloudWatch](https://aws.amazon.com/cloudwatch) events.

## How it Works

Using a [facebook page token](https://developers.facebook.com/docs/pages/access-tokens), a client to facebook's [Graph API](https://github.com/mobolic/facebook-sdk) requests upcoming events from the Boston DSA facebook page using the `/BostonDSA/events` REST API endpoint.

A hash is taken of each event returned by the request to compare to a private extended property in Google Calendar.

Next, using a [Google Service Account](https://cloud.google.com/iam/docs/understanding-service-accounts), a client to Google's [Calendar API](https://developers.google.com/calendar/v3/reference/) requests events in the same window as above using the `/v3/calendars/<calendarId>/events` REST API endpoint. Events are filtered by a private extended property that indicates the event's origin is the the facebook page, `BostonDSA`.

Events that appear in the request to Graph API, but not the request to Google are created. Events that are found in both requests, but have different hashes are updated in Google. Events that are returned by Google, but can no longer be found on facebook are deleted.

## Deployment

This repo is configured to [deploy automatically](./.travis.yml) on tagged releases, but manual deployment is also possible.

First, set up your `.env` file with make and fill in at least your AWS credentials

```bash
make .env
```

Build the Lambda deployment packages (requires Docker)

```bash
make zip
```

Generate plan for updating infrastructure

```bash
make plan
```

Apply changes

```bash
make apply
```
