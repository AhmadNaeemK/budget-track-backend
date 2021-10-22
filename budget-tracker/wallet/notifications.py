from django.conf import settings
from django.core.mail import send_mail


def send_mail_report(recipient_emails, subject, html_message, message):
    try:
        send_mail(subject=subject,
                  message=message,
                  html_message=html_message,
                  from_email=settings.SENDER_EMAIL,
                  recipient_list=recipient_emails,
                  fail_silently=False)
        print('mail sent')
    except Exception as e:
        print("Error: ", e)


def send_sms_notification(recipient_phn, message_body):
    try:
        settings.TWILIO_CLIENT.messages.create(
            body=message_body,
            from_=settings.PHN_NUM,
            to=recipient_phn
        )
    except Exception as e:
        print("SMS not sent: ", e)