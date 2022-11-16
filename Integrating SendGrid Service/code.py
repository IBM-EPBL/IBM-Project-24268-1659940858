import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

message = Mail(
    from_email='1912019@nec.edu.in',
    to_emails='1912019@nec.edu.in',
    subject='Sending with Twilio SendGrid is Fun',
    html_content='<strong>and easy to do anywhere, even with Python</strong>')
sg = SendGridAPIClient(os.environ.get('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'))
response = sg.send(message)
print(response.status_code)
print(response.body)
print(response.headers)
