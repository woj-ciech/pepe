import sys
from validate_email import validate_email
import json
from colorama import Fore
import Utilsy
import argparse
from argparse import RawTextHelpFormatter
import time
import Interactive
import requests
import os
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

desc = """                            ,=.
              ,=''''==.__.="  o".___
        ,=.=="                  ___/
  ,==.,"    ,          , \,===""
 <     ,==)  \"'"=._.==)  \
  `==''    `"           `\n
  clover/snark^
  http://ascii.co.uk/art/platypus
  
  Post Exploitation Pastebin Emails
  github.com/woj-ciech
  medium.com/@woj_ciech
  
  Example:
  python pepe.py --file <dump.txt> --interactive --whitelist
  python pepe.py --file <dump.txt> --modules hibp google trumail --elasticsearch --blacklist"""

parser = argparse.ArgumentParser(
    description=desc, formatter_class=RawTextHelpFormatter)

parser.add_argument("--file", help="Load file", default=None)
parser.add_argument("--stream", help="Stream Pastebin", action='store_true')
parser.add_argument("--interactive", help="Interactive mode", action='store_true')
parser.add_argument("--modules", help="Modules to check in non-interactive mode", nargs='+', type=str,
                    default="google hibp")
parser.add_argument("--elasticsearch", help="Output to ElasticSearch", action='store_true')
parser.add_argument("--whitelist", help="Whitelist", action="store_true")
parser.add_argument("--blacklist", help="Blacklist", action="store_true")

utilsy = Utilsy.Utilsy()

args = parser.parse_args()
file = args.file
stream = args.stream
interactive = args.interactive
modules = args.modules
elasticsearch = args.elasticsearch
whitelist = args.whitelist
blacklist = args.blacklist

if elasticsearch:
    utilsy.test_elastic_connection()

if not stream and not file:
    print(Fore.RED + "Choose stream or file" + Fore.RESET)
    sys.exit()

if not whitelist and not blacklist:
    print(Fore.RED + "You need to choose between whitelist and blacklist" + Fore.RESET)

with open('config.json', 'r+') as f:
    config = json.load(f)

if not os.path.exists(file):
    print(desc)
    print(Fore.RED + "File does not exist" + Fore.RESET)
    sys.exit()


c = 0
if stream:
    print(desc)
    while 1:
        paste = utilsy.get_paste()
        if paste:
            for link in paste:
                req = requests.get(link['scrape_url'])
                ##match = rule.match(data=req.content)
                splitted = req.text.splitlines()[0].split(":")
                print(link['scrape_url'])
                c = c + 1
                print(c)
                try:
                    if validate_email(splitted[0]) and splitted[1]:
                        username_domain_list = splitted[0].split('@')
                        if interactive:
                            interact = Interactive.Interactive()
                            print(Fore.GREEN + "Found email/pass leak")
                            print(link['scrape_url'])
                            print('-----------------------Found email ' + Fore.GREEN + splitted[
                                0] + Fore.RESET + " with password " + Fore.RED + splitted[
                                      1].rstrip() + Fore.RESET + "-----------------------")
                            interactive(username_domain_list[1], splitted[0], splitted[1], config, elasticsearch)
                        else:
                            if 'google' in modules:
                                utilsy.check_google(splitted[0], splitted[1], elasticsearch)
                            if "hibp" in modules:
                                utilsy.check_hibp(splitted[0], splitted[1], elasticsearch)
                            if 'pipl' in modules:
                                utilsy.check_pipl(splitted[0], splitted[1], elasticsearch)
                            if 'fullcontact' in modules:
                                utilsy.check_fullcontact(splitted[0], splitted[1], elasticsearch)
                except:
                    pass
            print("Sleeping for 2 minutes...")
            time.sleep(2 * 60)

elif file:
    print(desc)
    with open(file) as f:
        lines = f.readlines()
        ###only checks if first string before colon is email address and password is not empty
        first_email_password_list = lines[0].split(":")
        if validate_email(first_email_password_list[0]) and first_email_password_list[1]:
            for line in lines:
                fc = False
                ggg = False
                hibp = False
                trum = False

                email_password_list = line.split(':')
                username_domain_list = email_password_list[0].split('@')
                if whitelist:
                    if username_domain_list[1] in config['domains']['whitelist']:
                        print('-----------------------Found email ' + Fore.GREEN + email_password_list[
                            0] + Fore.RESET + " with password " + Fore.RED + email_password_list[
                                  1].rstrip() + Fore.RESET + "-----------------------")
                        if interactive:
                            interact = Interactive.Interactive()
                            interact.interactive(username_domain_list[1], email_password_list[0],
                                                 email_password_list[1], config, elastic=elasticsearch)
                        else:
                            if 'google' in modules:
                                ggg = utilsy.check_google(email_password_list[0], email_password_list[1], elasticsearch)
                            if "hibp" in modules:
                                hibp = utilsy.check_hibp(email_password_list[0], email_password_list[1], elasticsearch)
                            if 'pipl' in modules:
                                pipl = utilsy.check_pipl(email_password_list[0], elasticsearch)
                            if 'fullcontact' in modules:
                                fc = utilsy.check_fullcontact(email_password_list[0], password=email_password_list[1],
                                                              interactive_flag=False, elastic=elasticsearch)
                            if 'trumail' in modules:
                                trum = utilsy.test_mail(email_password_list[0])

                            utilsy.calc_score(email=email_password_list[0], google=ggg, fc=fc, hibp=hibp, trumail=trum)

                if blacklist:
                    if username_domain_list[1] not in config['domains']['blacklist']:
                        print('-----------------------Found email ' + Fore.GREEN + email_password_list[
                            0] + Fore.RESET + " with password " + Fore.RED + email_password_list[
                                  1].rstrip() + Fore.RESET + "-----------------------")
                        if interactive:
                            interact = Interactive.Interactive()
                            interact.interactive(username_domain_list[1], email_password_list[0],
                                                 email_password_list[1], config, elasticsearch)
                        else:
                            if 'google' in modules:
                                ggg = utilsy.check_google(email_password_list[0], email_password_list[1], elasticsearch)
                            if "hibp" in modules:
                                hibp = utilsy.check_hibp(email_password_list[0], email_password_list[1], elasticsearch)
                            if 'pipl' in modules:
                                pipl = utilsy.check_pipl(email_password_list[0], elasticsearch)
                            if 'fullcontact' in modules:
                                fc = utilsy.check_fullcontact(email_password_list[0], password=email_password_list[1],
                                                              interactive_flag=False, elastic=elasticsearch)
                            if 'trumail' in modules:
                                trum = utilsy.test_mail(email_password_list[0])

                            utilsy.calc_score(email=email_password_list[0], google=ggg, fc=fc, hibp=hibp, trumail=trum)
        else:
            print(desc)
            print(Fore.RED + "Check your file, dump has to be in email:password format.")
            f.close()
