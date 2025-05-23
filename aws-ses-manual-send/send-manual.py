import boto3
import time
from botocore.exceptions import ClientError
import logging
import os
from dotenv import load_dotenv

load_dotenv()
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)


def send_email_with_ses(
    aws_access_key_id,
    aws_secret_access_key,
    region_name,
    sender_email,
    recipient_email,
    subject,
    body_text,
    body_html=None,
):
    """
    Send an email using AWS SES.

    Args:
        aws_access_key_id (str): AWS access key ID
        aws_secret_access_key (str): AWS secret access key
        region_name (str): AWS region (e.g., 'us-east-1', 'us-west-2')
        sender_email (str): Verified sender email address
        recipient_email (str): Recipient email address
        subject (str): Email subject
        body_text (str): Plain text body
        body_html (str, optional): HTML body

    Returns:
        str: Message ID if successful, None if failed
    """

    ses_client = boto3.client(
        "ses",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name,
    )

    email_content = {
        "Subject": {"Data": subject, "Charset": "UTF-8"},
        "Body": {"Text": {"Data": body_text, "Charset": "UTF-8"}},
    }

    if body_html:
        email_content["Body"]["Html"] = {"Data": body_html, "Charset": "UTF-8"}

    try:
        response = ses_client.send_email(
            Source=f"Tioga Updates <{sender_email}>",
            Destination={"ToAddresses": [recipient_email]},
            Message=email_content,
            ReplyToAddresses=["istiogaopen@gmail.com"],
        )

        message_id = response["MessageId"]
        logger.info(f"Email sent successfully! Message ID: {message_id}")
        return message_id

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        logger.error(f"Failed to send email. Error: {error_code} - {error_message}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return None


def send_tioga_email(recipient_email):
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    REGION_NAME = os.getenv("AWS_REGION_NAME")
    print(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, REGION_NAME)
    SENDER_EMAIL = "noreply@email.istiogaopen.com"  # Must be verified in SES

    SUBJECT = "Tioga Road opening May 26th"
    BODY_TEXT = """
Hello beloved subscribers,

Tioga Road will open May 26th at 8am. Though sadly they won't be opening the road early for cyclists this year. 

You previously subscribed to this list on https://istiogaopen.com. If you have comments, questions, want to wish me a happy birthday, or want to be removed, please email istiogaopen@gmail.com.

Hoping you many great adventures,
Chase

P.S. I was a few hours late this year because my automated email doesn't work beyond 500 subscribers. Please forgive me.

P.P.S. For future years, if you are interested in getting covert intelligence *before* Yosemite announces anything, I found https://tiogawatch.wordpress.com to be a delightful resource.
    """

    message_id = send_email_with_ses(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=REGION_NAME,
        sender_email=SENDER_EMAIL,
        recipient_email=recipient_email,
        subject=SUBJECT,
        body_text=BODY_TEXT,
    )

    if message_id:
        print(f"Email sent successfully with Message ID: {message_id}")
    else:
        print("Failed to send email")


def get_emails_to_skip():
    with open("done_sending.txt", "r") as f:
        ret = set([x for x in f.read().split("\n")])
    return ret


def send_all_emails():
    RATE_LIMIT_PER_SECOND = 13  # One less then the 14 they have as a limit.
    count = 0
    last_sent_time = time.time()
    done_file = open("done_sending.txt", "a")
    emails_to_skip = get_emails_to_skip()
    with open("to_send.txt", "r") as f:
        for line in f.readlines():
            email = line.strip()
            if email in emails_to_skip:
                logger.info(f"Skipping {email}")
                continue
            logger.info(f"Sending to {email}")
            send_tioga_email(email)
            done_file.write(email + "\n")
            count += 1
            if count % RATE_LIMIT_PER_SECOND == 0:
                to_wait = max(0, 1 - (time.time() - last_sent_time))
                logger.info(f"Sleeping for {to_wait}s")
                time.sleep(to_wait)
                last_sent_time = time.time()
    done_file.close()


if __name__ == "__main__":
    # send_all_emails()
    send_tioga_email("theicfire@gmail.com")
