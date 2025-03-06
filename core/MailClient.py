import os
import smtplib
import ssl
import logging
from email import encoders
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class MailClient:
    def __init__(self, mail_host, mail_port, mail_user, mail_pass, mail_sender, mail_receiver, mail_subject,
                 mail_content, mail_files):
        self.mail_host = mail_host
        self.mail_user = mail_user
        self.mail_pass = mail_pass
        self.mail_port = mail_port
        self.sender = mail_sender
        self.receiver = mail_receiver
        self.subject = mail_subject
        self.content = mail_content
        self.files = mail_files

    def send_mail(self):
        msg = MIMEMultipart()
        msg['From'] = self.sender
        msg['To'] = self.receiver
        msg['Subject'] = self.subject
        msg.attach(MIMEText(self.content, 'plain', 'utf-8'))
        if self.files is not None:
            for file in self.files:
                with open(file, 'rb') as f:
                    attach_file = MIMEBase('application', 'octet-stream')
                    attach_file.set_payload(f.read())
                encoders.encode_base64(attach_file)
                attach_file.add_header('Content-Disposition', 'attachment',
                                       filename=Header(os.path.basename(file), 'utf-8').encode())
                msg.attach(attach_file)

        try:
            _context = ssl.create_default_context()
            smtp_obj = smtplib.SMTP_SSL(host=self.mail_host, port=self.mail_port, context=_context)
            smtp_obj.login(self.mail_user, self.mail_pass)
            smtp_obj.sendmail(self.sender, self.receiver.split(';'), msg.as_string())
            logging.info('邮件发送成功')
            return True
        except Exception as e:
            logging.error('Error: ' + str(e))
            return False

# if __name__ == '__main__':
#     host = 'smtp.qq.com'
#     port = 465
#     user = '1936343575@qq.com'
#     password = 'rmteqfcaejukehac'
#     sender = '1936343575@qq.com'
#     receiver = '18350229270@139.com;'
#     subject = '测试邮件'
#     content = '这是一封测试邮件，请勿回复。'
#     files = ["C:/Users/19363/Desktop/需求文档/安全报审/附件1：中国移动政企领域能力解耦标准（试行版）.pdf"]
#     mail_client = MailClient(mail_host=host, mail_port=port, mail_user=user, mail_pass=password,
#                              mail_sender=sender, mail_receiver=receiver, mail_subject=subject, mail_content=content,
#                              mail_files=files)
#     print(mail_client.send_mail())
