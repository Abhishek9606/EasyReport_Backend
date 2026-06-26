import random
from flask_mail import Mail, Message
import mysql.connector
import os

def generate_otp():
    return random.randint(100000,999999)


def get_db_connection():
    conn = mysql.connector.connect(
        host = os.environ.get("host"),
        user =  os.environ.get("user"),
        password =  os.environ.get("password"),
        database =  os.environ.get("database")
    )
    return conn


def configure_app(app):
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
    app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")
    mail = Mail(app)


def send_email(app,email,otp):
    email_message = Message(
         "Verify your email",
         sender=app.config['MAIL_USERNAME'],
         recipients=[email]
         )
        
    email_message.body = f"""
    Your verification OTP is {otp}
    """
    mail.send(email_message)


