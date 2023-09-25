import asyncio
import csv

from anticaptchaofficial.hcaptchaproxyless import *
from fake_useragent import UserAgent
# from playwright.async_api import async_playwright, Browser, ProxySettings
from playwright.async_api import Page, async_playwright, ProxySettings, expect
from python_anticaptcha import AnticaptchaClient, NoCaptchaTaskProxylessTask

from output import write_reddit_csv, write_verified_accs, write_active_emails
import socks

import imaplib
import email
from bs4 import BeautifulSoup
import re

gr = "\033[1;32m"
red = "\033[1;31m"
cy = "\033[1;36m"
red = "\033[91m"

users = []
accounts = []
mails = []
counter = 0
# user = {'mail_name': 'captchatest123@rambler.ru', 'mail_pass': 'Audi2834',
#         'proxy': 'http://vwwicapv:z9rsxacmive8@23.229.126.159:7688', 'acc_name': 'NeonNinjaXplorer13',
#         'acc_pass': 'TestPwd123!'}
# users.append(user)

CAPTCHA_API_KEY = '1a5c4f91a30ab5a09436947a7e49988b'
REDDIT_URL = 'https://old.reddit.com/register'
HCAPTCHA_SCRIPT_FILE_PATH = 'hcaptcha.js'
RAMBLER_URL = 'https://id.rambler.ru/login-20/login'
RAMBLER_HCAPTCHA_SITE_KEY = "322e5e22-3542-4638-b621-fa06db098460"
REDDIT_RECAPTCHA_SITE_KEY = "6LeTnxkTAAAAAN9QEuDZRpn90WwKk_R1TRW_g-JC"

with open("names.csv", encoding='UTF-8') as names_file:
    names_reader = csv.reader(names_file, lineterminator="\n")
    with open("passwords.csv", encoding='UTF-8') as passwords_file:
        passwords_reader = csv.reader(passwords_file, lineterminator="\n")
        with open("mailproxy.csv", encoding='UTF-8') as mail_proxy_file:
            mail_proxy_reader = csv.reader(mail_proxy_file, delimiter=";", lineterminator="\n")
            while True:
                names_row = next(names_reader, None)
                pass_row = next(passwords_reader, None)
                mail_proxy_row = next(mail_proxy_reader, None)
                if names_row is None or pass_row is None or mail_proxy_row is None:
                    break
                user = {'acc_name': names_row[0], 'acc_pass': pass_row[0], 'mail_name': mail_proxy_row[1],
                        'mail_pass': mail_proxy_row[2], 'proxy': mail_proxy_row[10], 'user_agent': mail_proxy_row[9]}
                users.append(user)

with open("output/reddit_accounts.csv", encoding="UTF-8") as accs_file:
    rows = csv.reader(accs_file, delimiter=";", lineterminator="\n")
    next(rows, None)
    for row in rows:
        account = {'acc_name': row[0], 'acc_pass': row[1], 'mail_name': row[2], 'mail_pass': row[3], 'proxy': row[4]}
        accounts.append(account)


def solve_hcaptcha(captcha_api_key, website_url, website_key):
    solver = hCaptchaProxyless()
    solver.set_verbose(1)
    solver.set_key(captcha_api_key)
    solver.set_website_url(website_url)
    solver.set_website_key(website_key)
    # solver.set_proxy_address("PROXY_ADDRESS")
    # solver.set_proxy_port(1234)
    # solver.set_proxy_login("proxylogin")
    # solver.set_proxy_password("proxypassword")
    # solver.set_user_agent("Mozilla/5.0")
    solver.set_cookies("test=true")

    # tell API that Hcaptcha is invisible
    # solver.set_is_invisible(1)

    # set here parameters like rqdata, sentry, apiEndpoint, endpoint, reportapi, assethost, imghost
    # solver.set_enterprise_payload({
    #    "rqdata": "rq data value from target website",
    #    "sentry": True
    # })

    # Specify softId to earn 10% commission with your app.
    # Get your softId here: https://anti-captcha.com/clients/tools/devcenter
    solver.set_soft_id(0)

    g_response = solver.solve_and_return_solution()
    if g_response != 0:
        print("[INFO] HCAPTCHA TOKEN = : " + g_response)
        return g_response
    else:
        print(red + "[ERROR] HCAPTCHA IS NOT SOLVED..." + solver.error_code)
        return None


def solve_recaptcha(api_key, reddit_url, reddit_site_key):
    print('[INFO] SOLVING REDDIT CAPTCHA...')
    client = AnticaptchaClient(api_key)
    task = NoCaptchaTaskProxylessTask(reddit_url, reddit_site_key)
    job = client.createTask(task)
    job.join()
    print('[INFO]  CAPTCHA RESPONSE...' + job.get_solution_response())
    return job.get_solution_response()


def parse_proxy(proxy_string):
    # Remove the "http://" prefix
    proxy_string = proxy_string.replace("http://", "")
    # Split the string at "@" to separate username, password, and the rest
    parts = proxy_string.split("@")
    # Extract the IP and Port from the last part
    ip_port = parts[-1]
    # Extract the username and password if they exist
    if len(parts) == 2:
        username, password = parts[0].split(":")
    else:
        username, password = None, None

    return f'http://{ip_port}', username, password


async def _set_captcha_token(page: Page, captcha_token: str):
    frame = await page.wait_for_selector('iframe[data-hcaptcha-widget-id]')
    await page.evaluate(
        'args => args[0].setAttribute("data-hcaptcha-response", args[1])',
        [frame, captcha_token],
    )
    await page.evaluate(
        'args => document.querySelector(args[0]).value = args[1]',
        ['textarea[name=h-captcha-response]', captcha_token],
    )
    await page.evaluate('code => hcaptcha.submit(code)', captcha_token)
    await page.wait_for_timeout(500)


async def create_browser(proxy_settings):
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False, proxy=proxy_settings)
    return browser


async def register_reddit_acc(user):
    proxy = user['proxy']
    acc_name = user['acc_name']
    acc_pass = user['acc_pass']
    mail_name = user['mail_name']
    mail_pass = user['mail_pass']
    user_agent = user['user_agent']
    ua = UserAgent()
    user_agent = ua.random
    http_proxy, username, password = parse_proxy(proxy)
    print(http_proxy, username, password)
    proxy_settings = ProxySettings(
        server=http_proxy,
        username=username,
        password=password,
    )
    browser = await create_browser(proxy_settings)
    context = await browser.new_context(proxy=proxy_settings, user_agent=user_agent)
    await context.clear_cookies()
    page = await context.new_page()
    await page.goto(REDDIT_URL)
    await page.locator('#user_reg').type(acc_name)
    await page.locator('#passwd_reg').type(acc_pass)
    await page.locator('#passwd2_reg').type(acc_pass)
    await page.locator('#email_reg').type(mail_name)
    await page.wait_for_timeout(70000)
    # captcha_response = solve_recaptcha(CAPTCHA_API_KEY, REDDIT_URL, REDDIT_RECAPTCHA_SITE_KEY)
    # captcha_input = await page.wait_for_selector('#g-recaptcha-response')
    # await page.evaluate('(element) => element.style.visibility = "visible";', captcha_input)
    # await captcha_input.type(captcha_response)
    # await page.locator('xpath=/html/body/div[3]/div/div/div[1]/form/div[8]/button').click()
    try:
        await page.click('button[type=submit]')
        await page.wait_for_timeout(10000)
        write_reddit_csv(acc_name, acc_pass, mail_name, mail_pass, proxy)
        await context.close()
        await browser.close()
    except:
        print(red + "[ERROR] REGISTREATION OF REDDIT ACCOUNT FAILED..." + acc_name + '  ' + mail_name)
        await context.close()
        await browser.close()


async def _verify_email(account, captcha_token, context):
    proxy = account['proxy']
    acc_name = account['acc_name']
    acc_pass = account['acc_pass']
    mail_name = account['mail_name']
    mail_pass = account['mail_pass']
    page = await context.new_page()
    await page.goto(RAMBLER_URL)
    await page.wait_for_timeout(1000)
    await page.locator("xpath=//input[@id='login']").type(mail_name)
    await page.locator("xpath=//*[@id='password']").type(mail_pass)
    await page.click("button[type=submit]")
    await _set_captcha_token(page, captcha_token)
    await page.wait_for_timeout(5000)
    await page.click('button[type=submit]')
    await page.wait_for_timeout(3000)
    await page.goto("https://mail.rambler.ru/folder/INBOX/2")
    await page.wait_for_timeout(3000)
    print("[INFO] TRYING TO VERIFY")
    link = await page.locator("xpath=//a[starts-with(@href, 'https://www.reddit.com/verification/')]").get_attribute(
        'href')
    await page.goto(link)
    await page.click('button[type=submit]')
    await page.wait_for_timeout(1000)
    write_verified_accs(acc_name, acc_pass, mail_name, mail_pass, proxy)
    print("[INFO] ACCOUNT VERIFIED")


async def verify_rambler_email(account):
    proxy = account['proxy']
    ua = UserAgent()
    user_agent = ua.random
    http_proxy, username, password = parse_proxy(proxy)
    print(http_proxy, username, password)
    proxy_settings = ProxySettings(
        server=http_proxy,
        username=username,
        password=password,
    )
    pr_browser = await create_browser(proxy_settings)
    context = await pr_browser.new_context(proxy=proxy_settings, user_agent=user_agent)
    await context.clear_cookies()
    await context.add_init_script(path='./js/hcaptcha.js')
    try:
        captcha_token = solve_hcaptcha(CAPTCHA_API_KEY, RAMBLER_URL, RAMBLER_HCAPTCHA_SITE_KEY)
        await _verify_email(account, captcha_token, context)
        await context.close()
        await pr_browser.close()
    except:
        print(red + "[ERROR] ACCOUNT NOT VERIFIED, TRYING AGAIN...")
        await context.close()
        await pr_browser.close()
        await verify_rambler_email(account)


async def read_email_imap():
    reddit_verification_pattern = re.compile(r'https://www\.reddit\.com/verification/[\w/]+')
    imap_server = "imap.rambler.ru"
    acc_name = account['acc_name']
    acc_pass = account['acc_pass']
    # mail_name = account['mail_name']
    # mail_pass = account['mail_pass']
    # mail_name = "captchatest123@rambler.ru"
    mail_name = "preh0kolid-f@rambler.ru"
    # mail_pass = "Audi2834"
    mail_pass = "ethHF!7Us0eH"
    proxy = account['proxy']
    # proxy_host = 'proxy_server_address'
    # proxy_port = 1080  # Change this to the proxy server's port number
    # proxy_type = socks.HTTP
    # proxy_username = 'your_proxy_username'
    # proxy_password = 'your_proxy_password'
    mail = imaplib.IMAP4_SSL(imap_server)
    mail.login(mail_name, mail_pass)
    mail.select("inbox")
    status, email_ids = mail.search(None, "ALL")
    email_ids = email_ids[0].split()
    for email_id in email_ids:
        status, msg_data = mail.fetch(email_id, "(RFC822)")
    # Parse the email message
    msg = email.message_from_bytes(msg_data[0][1])
    # Extract HTML content if available
    if msg.is_multipart():
        print('2')
        for part in msg.walk():
            print('3')
            if part.get_content_type() == "text/html":
                print('4')
                email_html = part.get_payload(decode=True).decode("utf-8")
                print('5')
                # Use BeautifulSoup to parse the HTML and find href links
                soup = BeautifulSoup(email_html, "html.parser")
                print('6')
                links = soup.find_all("a", href=True)
                print('7')
                # Extract and print href links
                for link in links:
                    href = link["href"]
                    if reddit_verification_pattern.match(href):
                        print("[INFO] FOUND REDDIT VERIFICATION LINK:", href)
                        # ua = UserAgent()
                        # user_agent = ua.random
                        # http_proxy, username, password = parse_proxy(proxy)
                        # print(http_proxy, username, password)
                        # proxy_settings = ProxySettings(
                        #     server=http_proxy,
                        #     username=username,
                        #     password=password,
                        # )
                        # pr_browser = await create_browser(proxy_settings)
                        # context = await pr_browser.new_context(proxy=proxy_settings, user_agent=user_agent)
                        # await context.clear_cookies()
                        # page = await context.new_page()
                        # try:
                        #     await page.goto(href)
                        #     # await page.click('button[type=submit]')
                        #     await page.wait_for_timeout(100000)
                        #     # write_verified_accs(acc_name, acc_pass, username, password, proxy)
                        #     await context.close()
                        #     await pr_browser.close()
                        # except:
                        #     print(red + "[ERROR] ACCOUNT NOT VERIFIED, SMTH WENT WRONG...")
    mail.logout()


async def verify_reddit_accs():
    print(accounts)
    for account in accounts:
        await verify_rambler_email(account)


async def verify_reddit_accs_imap():
    for account in accounts:
        await read_email_imap(account)
        # try:
        #     await read_email_imap(account)
        #     print("[INFO] ACCOUNT VERIFIED")
        # except:
        #     print(red + "[ERROR] ACCOUNT NOT VERIFIED, TRYING AGAIN...")


async def register_reddit_accs():
    print(users)
    for user in users:
        try:
            await register_reddit_acc(user)
        except:
            print(red + "[ERROR] MOVING TO ANOTHER ACCOUNT...")


# asyncio.run(register_reddit_accs())
# asyncio.run(verify_reddit_accs())
# asyncio.run(verify_reddit_accs_imap())
asyncio.run(read_email_imap())
