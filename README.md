# Boston DSA Facebook Event Sync

Sync BostonDSA facebook events to other calendars

This app runs as a scheduled job in [heroku](https://dashboard.heroku.com/apps/boston-dsa-event-sync).

*If you have access to the heroku app above, please treat the keys as secret*

## Prerequisites

Before beginning, you will need a host of API keys and endpoints to deploy this application.

You will need to create and configure a [facebook app](https://github.com/amancevice/fest/blob/master/docs/facebook.md#facebook) to acquire the access keys to use Graph API.

For Google, you will need to set up a [Google Cloud Service](https://github.com/amancevice/fest/blob/master/docs/google.md#google-cloud) account.

For WordPress, you will need to install the [Application Passwords](https://wordpress.org/plugins/application-passwords/) and [The Events Calendar](https://wordpress.org/plugins/event-tickets/) plugins. Read the [WordPress](https://github.com/amancevice/fest/blob/master/docs/wordpress.md#wordpress) docs for more information.

## Deployment

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

Deploy this app to heroku and use the heroku scheduler to run the sync job on a cron.

Once the app is deployed, you will need to configure the environmental variables above. Use the heroku web console, or the terminal.

For facebook:

```bash
heroku config:set FACEBOOK_APP_ID='<facebook-app-id>'
heroku config:set FACEBOOK_APP_SECRET='<facebook-app-secret>'
heroku config:set FACEBOOK_PAGE_ID='<facebook-page-id-or-alias>'
```

For Google:

```bash
heroku config:set GOOGLE_ACCOUNT_TYPE='service_account'
heroku config:set GOOGLE_CALENDAR_ID='<optional-google-calendar-id>'
heroku config:set GOOGLE_CLIENT_EMAIL='<google-service-client-email>'
heroku config:set GOOGLE_CLIENT_ID='<google-client-id>'
heroku config:set GOOGLE_PRIVATE_KEY='<google-private-key-multi-line-string'
heroku config:set GOOGLE_PRIVATE_KEY_ID='<google-private-key-id'
heroku config:set GOOGLE_SCOPE='https://www.googleapis.com/auth/calendar'
```

For WordPress:

```bash
heroku config:set WORDPRESS_ENDPOINT='<wordpress-host>/xmlrpc.php'
heroku config:set WORDPRESS_USERNAME='<wordpress-user>'
heroku config:set WORDPRESS_APP_PASSWORD='<wordpress-app-password>'
```

For The Events Calendar Plugin:

```bash
heroku config:set TRIBE_ENDPOINT='<wordpress-host>/wp-json/tribe/events/v1'
```

If using the Dead Man's Snitch plugin:

```bash
heroku config:set DEADMANSSNITCH_URL='<dead-mans-snitch-ping-url>'
```
