import random
from flask_mail import Mail, Message
import mysql.connector
import os
from dotenv import load_dotenv
import pymysql

load_dotenv()

def generate_otp():
    return random.randint(100000,999999)

def get_db_connection():
    timeout = 10
    connection = pymysql.connect(
        charset="utf8mb4",
        connect_timeout=timeout,
        cursorclass=pymysql.cursors.DictCursor,
        db=os.environ.get("database"),
        host=os.environ.get("host"),
        password=os.environ.get("password")
        read_timeout=timeout,
        port=13285,
        user=os.environ.get("user"),
        write_timeout=timeout,
        )

    return connection


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
    email.send(email_message)


