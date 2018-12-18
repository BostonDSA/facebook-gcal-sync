provider archive {
  version = "~> 1.1"
}

provider aws {
  access_key = "${var.aws_access_key_id}"
  secret_key = "${var.aws_secret_access_key}"
  profile    = "${var.aws_profile}"
  region     = "${var.aws_region}"
  version    = "~> 1.52"
}

locals {
  app_name = "facebook-gcal-sync"
}

data archive_file alarm {
  type        = "zip"
  source_file = "${path.module}/alarm.py"
  output_path = "${path.module}/dist/package-alarm.zip"
}

data aws_iam_policy_document assume_role {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com", "lambda.amazonaws.com"]
    }
  }
}

data aws_iam_policy_document inline {
  statement {
    sid       = "InvokeFunction",
    actions   = ["lambda:InvokeFunction"]
    resources = ["${aws_lambda_function.lambda.arn}"]
  }

  statement {
    sid       = "GetSecretValues"
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [
      "${data.aws_secretsmanager_secret.facebook.arn}",
      "${data.aws_secretsmanager_secret.google.arn}",
    ]
  }

  statement {
    sid       = "PublishToSns"
    actions   = ["sns:Publish"]
    resources = ["${data.terraform_remote_state.socialismbot.slack_post_message_topic_arn}"]
  }

  statement {
    sid       = "WriteLogs"
    actions   = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["*"]
  }
}

data aws_secretsmanager_secret facebook {
  name = "${var.facebook_secret_name}"
}

data aws_secretsmanager_secret google {
  name = "${var.google_secret_name}"
}

data terraform_remote_state socialismbot {
  backend = "s3"

  config {
    bucket  = "boston-dsa-terraform"
    key     = "socialismbot.tfstate"
    region  = "us-east-1"
    profile = "bdsa"
  }
}

resource aws_cloudwatch_event_rule rule {
  description         = "Sync facebook events with Google Calendar"
  is_enabled          = "${var.event_rule_is_enabled}"
  name                = "${aws_lambda_function.lambda.function_name}"
  role_arn            = "${aws_iam_role.role.arn}"
  schedule_expression = "${var.event_rule_schedule_expression}"
}

resource aws_cloudwatch_event_target target {
  arn      = "${aws_lambda_function.lambda.arn}"
  input    = "{}"
  rule     = "${aws_cloudwatch_event_rule.rule.name}"
}

resource aws_cloudwatch_log_group logs {
  name              = "/aws/lambda/${aws_lambda_function.lambda.function_name}"
  retention_in_days = 30
}

resource aws_cloudwatch_log_group alarm {
  name              = "/aws/lambda/${aws_lambda_function.alarm.function_name}"
  retention_in_days = 30
}

resource aws_cloudwatch_metric_alarm alarm {
  alarm_actions             = ["${aws_sns_topic.alarm.arn}"]
  alarm_description         = "${local.app_name} is failing"
  alarm_name                = "${local.app_name}"
  comparison_operator       = "GreaterThanOrEqualToThreshold"
  evaluation_periods        = "6"
  metric_name               = "FailedInvocations"
  namespace                 = "AWS/Events"
  ok_actions                = ["${aws_sns_topic.alarm.arn}"]
  period                    = "3600"
  statistic                 = "Sum"
  threshold                 = "1"
  treat_missing_data        = "notBreaching"

  dimensions {
    RuleName = "${aws_cloudwatch_event_rule.rule.name}"
  }
}

resource aws_iam_role role {
  description        = "Access to facebook, Google, and AWS resources."
  name               = "${local.app_name}"
  assume_role_policy = "${data.aws_iam_policy_document.assume_role.json}"
}

resource aws_iam_role_policy inline {
  name   = "${aws_iam_role.role.name}"
  policy = "${data.aws_iam_policy_document.inline.json}"
  role   = "${aws_iam_role.role.name}"
}

resource aws_lambda_function lambda {
  description      = "Synchronize facebook page events with Google Calendar"
  filename         = "${path.module}/dist/package.zip"
  function_name    = "${local.app_name}"
  handler          = "lambda.handler"
  role             = "${aws_iam_role.role.arn}"
  runtime          = "python3.7"
  source_code_hash = "${base64sha256(file("${path.module}/dist/package.zip"))}"
  timeout          = 15

  environment {
    variables {
      FACEBOOK_PAGE_ID   = "${var.facebook_page_id}"
      FACEBOOK_SECRET    = "${var.facebook_secret_name}"
      GOOGLE_CALENDAR_ID = "${var.google_calendar_id}"
      GOOGLE_SECRET      = "${var.google_secret_name}"
      SLACK_CHANNEL      = "${var.slack_channel_events}"
      SLACK_FOOTER_ICON  = "${var.slack_footer_icon}"
      SLACK_FOOTER_URL   = "${var.slack_footer_url}"
      SLACK_TOPIC_ARN    = "${data.terraform_remote_state.socialismbot.slack_post_message_topic_arn}"
    }
  }
}

resource aws_lambda_function alarm {
  description      = "Publish Slack message when ${local.app_name} is failing"
  filename         = "${data.archive_file.alarm.output_path}"
  function_name    = "${local.app_name}-alarm"
  handler          = "alarm.handler"
  role             = "${aws_iam_role.role.arn}"
  runtime          = "python3.7"
  source_code_hash = "${data.archive_file.alarm.output_base64sha256}"

  environment {
    variables {
      SLACK_AUTHOR_ICON = "${var.slack_author_icon}"
      SLACK_CHANNEL     = "${var.slack_channel_alarms}"
      SLACK_FOOTER_ICON = "${var.slack_footer_icon}"
      SLACK_FOOTER_URL  = "${var.slack_footer_url}"
      SLACK_TOPIC_ARN   = "${data.terraform_remote_state.socialismbot.slack_post_message_topic_arn}"
    }
  }
}

resource aws_lambda_permission trigger {
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.lambda.function_name}"
  principal     = "events.amazonaws.com"
  source_arn    = "${aws_cloudwatch_event_rule.rule.arn}"
}

resource aws_lambda_permission alarm {
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.alarm.function_name}"
  principal     = "sns.amazonaws.com"
  source_arn    = "${aws_sns_topic.alarm.arn}"
}

resource aws_sns_topic alarm {
  name = "${replace(local.app_name, "-", "_")}_alarm"
}

resource aws_sns_topic_subscription alarm {
  topic_arn = "${aws_sns_topic.alarm.arn}"
  protocol  = "lambda"
  endpoint  = "${aws_lambda_function.alarm.arn}"
}
