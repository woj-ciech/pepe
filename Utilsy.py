import json
import smtplib
import ssl
import time

import pyhibp
import requests
from colorama import Fore
from elasticsearch import Elasticsearch
from fullcontact import FullContact
from googlesearch import search
from piplapis.search import SearchAPIRequest
from pushsafer import Client, init
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import sys

with open('config.json', 'r') as f:
    conf = json.load(f)


# noinspection PyPep8,PyPep8
class Utilsy:

    def get_paste(self):
        try:
            # Create the API uri
            url = 'https://scrape.pastebin.com/api_scraping.php?limit=200'
            req = requests.get(url)

            if 'DOES NOT HAVE ACCESS' in req.text:
                print(
                    Fore.RED + "Your IP is not whitelisted" + Fore.RESET + " go to https://pastebin.com/doc_scraping_api")
                return []
            paste_json = json.loads(req.content)
            return paste_json
        except Exception as e:
            print(Fore.RED + str(e) + Fore.RESET)
            return False

    def check_google(self, email, password, elastic=False):
        print('---' + Fore.CYAN + 'Google Search' + Fore.RESET + '---')
        to_elastic = {"email": email, "password": password, "results": []}
        try:
            for url in search("\"" + email + "\"", stop=10, tbs="li:1"):
                to_elastic['results'].append(url)
                print(url)

        except Exception as e:
            print(str(e) + Fore.RESET)

        if len(to_elastic['results']) > 0:
            if elastic:
                self.put_elastic('google', 'email', to_elastic)
            return True
        else:
            print(Fore.RED + "Nothing found" + Fore.RESET)
            return False

    def calc_score(self, email, google=None, fc=None, hibp=None, trumail=None):
        if fc:
            print("Found social media profile, sending notification")
            social_string = " ".join(str(x) for x in fc)
            self.send_push("Found email " + email + " with following social media: " + social_string)

    def check_hibp(self, email, password, elastic=False):
        print("---" + Fore.CYAN + "Have I Been Pwned" + Fore.RESET + "---")
        to_elastic = {"email": email, "password": password, "results": []}
        try:
            resp = pyhibp.get_account_breaches(account=email, truncate_response=True)
            if resp:
                for name in resp:
                    to_elastic['results'].append(name['Name'])
                    print(Fore.MAGENTA + name['Name'] + Fore.RESET)
            else:
                print(Fore.RED + "Nothing found" + Fore.RESET)
        except Exception as e:
            print(Fore.RED + str(e) + Fore.RESET)

        if len(to_elastic['results']) > 0:
            if elastic:
                self.put_elastic('hibp', 'email', to_elastic)
            return True
        else:
            return False

    def send_push(self, message):
        try:
            init(privatekey=conf['keys']['pushsafer'])
            client = Client("")
            client.send_message(message=message, title="Found", device='a', sound="1", icon="20", vibration="2",
                                answer=0,
                                picture1=None, picture2=None, picture3=None, expire=None, time2live=None, url="",
                                retry=None,
                                urltitle=None, priority=5)
            print("Push notification has been send")
        except Exception as e:
            print(Fore.RED + str(e) + Fore.RESET)

    def check_fullcontact(self, email, password, interactive_flag=False, elastic=False):
        print("---" + Fore.CYAN + "FullContact" + Fore.RESET + "---")
        fc = FullContact(conf['keys']['fullcontact'])
        person = fc.person(email=email)
        decoded_person_json = person.content.decode("utf-8")
        person_json = json.loads(decoded_person_json)
        social_to_push = []
        to_elastic = {"email": email, "password": password}

        try:
            if person_json['status'] == 200:
                if 'contactInfo' in person_json:
                    if 'fullName' in person_json['contactInfo']:
                        print(person_json['contactInfo']['fullName']
                              )

                if 'socialProfiles' in person_json:
                    for social in person_json['socialProfiles']:
                        social_to_push.append(social['url'])
                        print(social['url'])

                if 'demographics' in person_json:
                    if 'locationGeneral' in person_json['demographics']:
                        print(person_json['demographics']['locationGeneral'])

                to_elastic.update(person_json)
                if elastic:
                    self.put_elastic('fullcontact', 'email', to_elastic)

            elif person_json['status'] == 202:
                if interactive_flag:
                    time_dec = input("Your search is queued, do you want to wait for 2 minutes? [Y/N] \n> ")
                    if time_dec == "Y":
                        print("Sleeping...")
                        time.sleep(60 * 2)
                        self.check_fullcontact(email, elastic)
                    else:
                        pass

            else:
                print("No results")

        except Exception as e:
            print(Fore.RED + str(e) + Fore.RESET)

        if len(social_to_push) > 0 and interactive_flag:
            return social_to_push
        else:
            return False

    def save_config(self, config):
        with open('config.json', 'w') as f:
            json.dump(config, f)
        print("Config has been saved")

    def check_pipl(self, email, password, elastic=False):
        print("---" + Fore.CYAN + "Pipl" + Fore.RESET + '---')
        request = SearchAPIRequest(email=email,
                                   show_sources=True, use_https=True, api_key=conf['keys']['pipl'])
        to_elastic = {"email": email, "password": password, "name": [], "dob": "", 'jobs': [], 'addresses': [],
                      "images": [], "urls": []}
        try:
            response = request.send()
            if response.person:
                if response.person.names:
                    print("Name: " + response.person.names[0].display)
                    for name in response.person.names:
                        to_elastic['name'].append(name.display)
                if response.person.dob:
                    print(response.person.dob.display)
                    to_elastic['dob'].append(str(response.person.dob.display))
                if response.person.jobs:
                    print("Jobs:")
                    for job in response.person.jobs:
                        # if "Director" in job.display or "CEO" in job.display
                        # self.send_push("Found big fish " + email + password)

                        print(job.display)
                if response.person.urls:
                    for url in response.person.urls:
                        print(url.display)
                        to_elastic['urls'].append(url.display)

                for address in response.person.addresses:
                    to_elastic['addresses'].append(address.display)

                for image in response.person.images:
                    to_elastic['images'].append(image.display)

                if elastic:
                    self.put_elastic('pipl', 'email', to_elastic)
            else:
                print("Nothing was found :(")
        except Exception as e:
            print(Fore.RED + str(e) + Fore.RESET)

    def test_mail(self, email):
        print("---" + Fore.CYAN + "Trumail" + Fore.RESET + '---')
        req_trumail = requests.get("https://api.trumail.io/v2/lookups/json?email=" + email)
        json_trumail = json.loads(req_trumail.content)
        try:
            if not json_trumail['validFormat']:
                print(Fore.RED + "[*] Wrong email format")
                return False
            elif not json_trumail['deliverable']:
                print("It seems like email address " + email + " is not deliverable")
            elif not json_trumail['hostExists']:
                print(email + " may be not real because host does not exists" + Fore.RESET)
            else:
                print(Fore.GREEN + "Email test passed" + Fore.RESET)
                return True
        except KeyError:
            print(Fore.RED + 'Rate limit' + Fore.RESET)

    def send_mail(self, email, password):
        print("Sending email to " + Fore.GREEN + email + Fore.RESET)
        port = 587  # For starttls
        smtp_server = "smtp.gmail.com"
        sender_email = conf['gmail']['username']  # from config
        receiver_email = email  # from paste
        account_password = conf['gmail']['password']  # password to account
        msg = conf['gmail']['message']
        message = 'Subject: {}\n\n{}'.format("You password has been leaked", msg)

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_server, port) as server:
                server.ehlo()  # Can be omitted
                server.starttls(context=context)
                server.ehlo()  # Can be omitted
                server.login(sender_email, account_password)
                server.sendmail(sender_email, receiver_email, message.replace("!PASSWORD!", password))
                print(Fore.MAGENTA + "Email has been sent successfully\n" + Fore.RESET)
        except Exception as e:
            print(Fore.RED + str(e) + Fore.RESET)

    def test_elastic_connection(self):

        es = Elasticsearch(host=conf['elasticsearch']['host'], port=conf['elasticsearch']['port'])

        if not es.ping():
            print('Unable to connect to Elasticsearch. \nCheck your connection and settings.json file')
            sys.exit()
        else:
            print("Succesfully connected to ElasticSearch")
            return es

    def put_elastic(self, index, doc_type, body):
        es = Elasticsearch(host=conf['elasticsearch']['host'], port=conf['elasticsearch']['port'])
        # es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
        ids = []
        print("[*] Saving output to Elasticsearch")
        try:
            resp = es.search(index=index)
            for i in resp['hits']['hits']:
                int_id = int(i['_id'])
                ids.append(int_id)

            last_id = max(ids)

            es.index(index=index, doc_type=doc_type, id=last_id + 1, body=body)
            print(Fore.GREEN + "Success" + Fore.RESET)
        except Exception as e:
            try:
                es.index(index=index, doc_type=doc_type, id=1, body=body)
                print(Fore.GREEN + "Success" + Fore.RESET)
            except Exception as e:
                print(Fore.RED + str(e) + Fore.RESET)
