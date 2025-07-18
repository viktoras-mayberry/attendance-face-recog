from flask_mail import Mail, Message
from flask import current_app

mail = Mail()

def init_mail(app):
    mail.init_app(app)


def send_email(subject, recipients, body, html=None):
    msg = Message(subject, recipients=recipients, body=body, html=html)
    mail.send(msg)


def send_attendance_report_email(recipient, report_text, report_html=None):
    subject = 'Your Attendance Report'
    send_email(subject, [recipient], report_text, html=report_html) 