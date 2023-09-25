import csv
import os


def write_reddit_csv(acc_name,
                     acc_pass,
                     mail_name,
                     mail_pass,
                     # user.ua,
                     proxy):
    csv_filename = 'reddit_accounts.csv'
    csv_filepath = f"output/{csv_filename}"
    headers = [
        "Reddit_Acc_Name",
        "Reddit_Acc_Pass",
        "Email_Name",
        "Email_Pass"
        # "User Agent",
        "Proxy",
    ]

    # Проверка существования файла
    file_exists = os.path.isfile(csv_filepath)

    with open(csv_filepath, mode="a", encoding='utf-8', newline='') as file:
        file_writer = csv.writer(file, delimiter=";")

        # Если файл не существует, добавляем заголовки
        if not file_exists:
            file_writer.writerow(headers)

        row = [
            acc_name,
            acc_pass,
            mail_name,
            mail_pass,
            # user.ua,
            proxy,
        ]

        file_writer.writerow(row)


def write_verified_accs(acc_name,
                     acc_pass,
                     mail_name,
                     mail_pass,
                     # user.ua,
                     proxy):
    csv_filename = 'reddit_verified_accounts.csv'
    csv_filepath = f"output/{csv_filename}"
    headers = [
        "Reddit_Acc_Name",
        "Reddit_Acc_Pass",
        "Email_Name",
        "Email_Pass"
        # "User Agent",
        "Proxy",
        "Verified"
    ]

    # Проверка существования файла
    file_exists = os.path.isfile(csv_filepath)

    with open(csv_filepath, mode="a", encoding='utf-8', newline='') as file:
        file_writer = csv.writer(file, delimiter=";")

        # Если файл не существует, добавляем заголовки
        if not file_exists:
            file_writer.writerow(headers)

        row = [
            acc_name,
            acc_pass,
            mail_name,
            mail_pass,
            # user.ua,
            proxy,
            "verified"
        ]

        file_writer.writerow(row)


def write_active_emails(mail_name,
                        mail_pass,
                        proxy):
    csv_filename = 'active_emails.csv'
    csv_filepath = f"output/{csv_filename}"
    headers = [
        "Email_Name",
        "Email_Pass"
        "Proxy",
    ]

    # Проверка существования файла
    file_exists = os.path.isfile(csv_filepath)

    with open(csv_filepath, mode="a", encoding='utf-8', newline='') as file:
        file_writer = csv.writer(file, delimiter=";")

        # Если файл не существует, добавляем заголовки
        if not file_exists:
            file_writer.writerow(headers)

        row = [
            mail_name,
            mail_pass,
            proxy,
        ]

        file_writer.writerow(row)