terraform {
  backend "s3" {
    bucket = "terraform.bostondsa.org"
    key    = "actionnetwork-airtable-sync.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = "us-east-1"
  assume_role {
    role_arn = var.AWS_ROLE_ARN
  }
}

locals {
  app_name                       = "actionnetwork-airtable-sync"
  event_rule_schedule_expression = "rate(1 hour)"
  event_rule_is_enabled          = true
  repo                           = "https://github.com/BostonDSA/facebook-gcal-sync"

  slack_channels = {
    cmt_tech_infra = "C7F7YRQUC"
    events         = "C7F7Z0WJG"
    testing        = "GB1SLKKL7"
  }

  tags = {
    App     = local.app_name
    Version = var.VERSION
    Repo    = local.repo
  }
}

/* IAM - Access to AWS resources for sync/alarm
 *
 * Can be assumed by CloudWatch & Lambda
 * Grant permission to invoke sync Lambda from from CloudWatch
 * Grant permission to get ActionNetwork/Airtable secrets from Lambda
 * Grant permission to publish to SNS topic to send Slack messages
 * Grant permission to write CloudWatch logs
 */
data "aws_iam_policy_document" "assume_role" {
  statement {
    actions = [
      "sts:AssumeRole",
    ]

    principals {
      type = "Service"

      identifiers = [
        "events.amazonaws.com",
        "lambda.amazonaws.com",
      ]
    }
  }
}

data "aws_iam_policy_document" "inline" {
  statement {
    sid = "InvokeFunction"

    actions = [
      "lambda:InvokeFunction",
    ]

    resources = [
      aws_lambda_function.sync.arn,
    ]
  }

  statement {
    sid = "GetSecretValues"

    actions = [
      "secretsmanager:GetSecretValue",
    ]

    resources = [
      data.aws_secretsmanager_secret.action_network.arn,
      data.aws_secretsmanager_secret.airtable.arn,
    ]
  }

  statement {
    sid = "PublishToSns"

    actions = [
      "sns:Publish",
    ]

    resources = [
      data.aws_sns_topic.socialismbot.arn,
    ]
  }

  statement {
    sid = "WriteLogs"

    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = [
      "*",
    ]
  }
}

data "aws_secretsmanager_secret" "action_network" {
  name = "actionnetwork/production"
}

data "aws_secretsmanager_secret" "airtable" {
  name = "airtable/production"
}

data "aws_sns_topic" "socialismbot" {
  name = "slack-socialismbot"
}

resource "aws_iam_role" "role" {
  description        = "Access to ActionNetwork, Airtable, and AWS resources."
  name               = local.app_name
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource "aws_iam_role_policy" "role_policy" {
  name   = aws_iam_role.role.name
  policy = data.aws_iam_policy_document.inline.json
  role   = aws_iam_role.role.name
}

/* SYNC - Sync ActionNetwork events to Airtable
 *
 * CloudWatch event rule runs on schedule
 * CloudWatch event target triggers Lambda function
 * Lambda function syncs events and posts to Slack SNS topic
 */

resource "aws_cloudwatch_event_rule" "sync" {
  description         = "Sync Action Network events with Airtable"
  is_enabled          = local.event_rule_is_enabled
  name                = aws_lambda_function.sync.function_name
  role_arn            = aws_iam_role.role.arn
  schedule_expression = local.event_rule_schedule_expression
}

resource "aws_cloudwatch_event_target" "sync" {
  arn   = aws_lambda_function.sync.arn
  input = "{}"
  rule  = aws_cloudwatch_event_rule.sync.name
}

resource "aws_cloudwatch_log_group" "sync" {
  name              = "/aws/lambda/${aws_lambda_function.sync.function_name}"
  retention_in_days = 30
}

resource "aws_lambda_function" "sync" {
  description      = "Synchronize Action Network events with Airtable"
  filename         = "dist/sync.zip"
  function_name    = local.app_name
  handler          = "sync.handler"
  role             = aws_iam_role.role.arn
  runtime          = "python3.11"
  source_code_hash = filebase64sha256("dist/sync.zip")
  tags             = local.tags
  timeout          = 900

  environment {
    variables = {
      SLACK_CHANNEL            = local.slack_channels["events"]
      SLACK_FOOTER_URL         = local.repo
      SLACK_TOPIC_ARN          = data.aws_sns_topic.socialismbot.arn
      ACTION_NETWORK_SECRET_ID = data.aws_secretsmanager_secret.action_network.name
      AIRTABLE_SECRET_ID       = data.aws_secretsmanager_secret.airtable.name
    }
  }
}

resource "aws_lambda_permission" "sync" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.sync.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.sync.arn
}

/* ALARM - Send a Slack alert when sync is failing
 *
 * CloudWatch metric alarm publishes message to SNS
 * SNS triggers subscribed Lambda function
 * Lambda composes message and publishes to @Socialismbot
 */

resource "aws_cloudwatch_log_group" "alarm" {
  name              = "/aws/lambda/${aws_lambda_function.alarm.function_name}"
  retention_in_days = 30
}

resource "aws_cloudwatch_metric_alarm" "alarm" {
  alarm_actions       = [aws_sns_topic.alarm.arn]
  alarm_description   = "${local.app_name} is failing"
  alarm_name          = local.app_name
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "6"
  metric_name         = "FailedInvocations"
  namespace           = "AWS/Events"
  ok_actions          = [aws_sns_topic.alarm.arn]
  period              = "3600"
  statistic           = "Sum"
  threshold           = "1"
  treat_missing_data  = "notBreaching"

  dimensions = {
    RuleName = aws_cloudwatch_event_rule.sync.name
  }
}

resource "aws_lambda_function" "alarm" {
  description      = "Publish Slack message when ${local.app_name} is failing"
  filename         = "dist/alarm.zip"
  function_name    = "${local.app_name}-alarm"
  handler          = "alarm.handler"
  role             = aws_iam_role.role.arn
  runtime          = "python3.11"
  source_code_hash = filebase64sha256("dist/alarm.zip")
  tags             = local.tags

  environment {
    variables = {
      SLACK_CHANNEL    = local.slack_channels["cmt_tech_infra"]
      SLACK_FOOTER_URL = local.repo
      SLACK_TOPIC_ARN  = data.aws_sns_topic.socialismbot.arn
    }
  }
}

resource "aws_lambda_permission" "alarm" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.alarm.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.alarm.arn
}

resource "aws_sns_topic" "alarm" {
  name = "${replace(local.app_name, "-", "_")}_alarm"
}

resource "aws_sns_topic_subscription" "alarm" {
  topic_arn = aws_sns_topic.alarm.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.alarm.arn
}

output "alarm_function_arn" {
  description = "Alarm Lambda function ARN"
  value       = aws_lambda_function.alarm.arn
}

output "alarm_function_name" {
  description = "Alarm Lambda function name"
  value       = aws_lambda_function.alarm.function_name
}

output "sync_function_arn" {
  description = "Sync Lambda function ARN"
  value       = aws_lambda_function.sync.arn
}

output "sync_function_name" {
  description = "Sync Lambda function name"
  value       = aws_lambda_function.sync.function_name
}

variable "VERSION" {
  description = "Release tag name"
}

variable "AWS_ROLE_ARN" {
  description = "AWS Role ARN to assume"
}
