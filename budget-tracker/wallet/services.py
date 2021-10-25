from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .models import TransactionCategories



def send_scheduled_transaction_report_mail(transaction, status):
    html = render_to_string('emails/scheduledTransactionReportTemplate.html',
                            {
                                'title': transaction.title,
                                'category': TransactionCategories.choices[transaction.category][1],
                                'amount': transaction.amount,
                                'status': status,
                                'remaining': transaction.cash_account.balance,
                            }
                            )
    send_mail(
        subject='Scheduled Transaction ' + status,
        message="Scheduled Transaction has " + status,
        html_message=html,
        recipient_list=[transaction.user.email],
        from_email=settings.SENDER_EMAIL
    )


def send_scheduled_transaction_report_sms(transaction, status):
    message = 'Scheduled Transaction for {title} has {status}' + \
              '\nTransaction Amount: {amount}' \
              '\nFrom BudgetTracker'

    settings.TWILIO_CLIENT.messages.create(
        body=message.format(title=transaction.title,
                            status=status,
                            amount=transaction.amount),
        from_=settings.PHN_NUM,
        to=transaction.user.phone_number
    )


def send_split_expense_payment_report_mail(split, user, split_payment, paid_amount, payment):
    html_message = render_to_string('emails/splitPaymentReportTemplate.html',
                                    {
                                        'title': split.title,
                                        'category': TransactionCategories.choices[split.category][1],
                                        'total_split': split_payment,
                                        'payment': payment,
                                        'rem_payment': (
                                                split_payment - paid_amount - payment
                                        ),
                                    }
                                    )

    title = "Payment for {split_title} paid by {user}".format(split_title=split.title,
                                                              user=user.username)
    send_mail(subject=title,
              message=title,
              html_message=html_message,
              recipient_list=[split.paying_friend.email],
              from_email=settings.SENDER_EMAIL
              )


def send_split_expense_payment_report_sms(split, user, payment):
    message = 'Payment {payment} for {title} made by {user}, added to your cash account' \
              '\nFrom BudgetTracker'

    settings.TWILIO_CLIENT.messages.create(
        body=message.format(title=split.title,
                            user=user.username,
                            payment=payment.amount),
        from_=settings.PHN_NUM,
        to=split.paying_friend.phone_number
    )


def send_split_include_notification_mail(split):
    html_message = render_to_string('emails/splitIncludeNotificationTemplate.html',
                                    {
                                        'title': split.title,
                                        'category': TransactionCategories.choices[split.category][1],
                                        'total_amount': split.total_amount,
                                        'paying_friend': split.paying_friend.username
                                    }
                                    )
    title = "{split_title} paid by {split_creator}".format(split_title=split.title,
                                                           split_creator=split.creator.username)
    send_mail(subject=title,
              message=title,
              html_message=html_message,
              recipient_list=split.all_friends_involved.all(),
              from_email=settings.SENDER_EMAIL
              )


def send_split_include_notification_sms(split):
    message = 'You have been added to a split expense for {title} by {creator}.\n' \
              '\n Amount Paid by {paying_friend}: {total_amount}' \
              '\n From BudgetTracker'
    for friend in split.all_friends_involved.all():
        settings.TWILIO_CLIENT.messages.create(
            body=message.format(title=split.title,
                                creator=split.creator.username,
                                paying_friend=split.paying_friend.username,
                                total_amount=split.total_amount),
            from_=settings.PHN_NUM,
            to=friend.phone_number
        )