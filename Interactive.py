import Utilsy
from colorama import Fore
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

utilsy = Utilsy.Utilsy()


class Interactive:

    def interactive(self, domain, email, password, config, elastic):
        next = None
        text_input = "[A] Add domain " + Fore.BLUE + domain + Fore.RESET + " to blacklist\n[T] Test\n[G] Google search\n[H] HaveIBeenPwned\n[P] Pipl\n[F] FullContact\n[I] Inform\n[N] Next\n> "
        choice = input(text_input)
        while not next:
            # print(Fore.GREEN + email + Fore.RESET)
            if choice == "A":
                config['domains']['blacklist'].append(domain)
                print(
                    'Domain ' + Fore.BLUE + domain + Fore.RESET + ' has been added to blacklist and will be no longer checked\n')
                utilsy.save_config(config)
                choice = input(
                    "[T] Test\n[G] Google search\n[H] HaveIBeenPwned\n[P] Pipl\n[F] FullContact\n[I] Inform\n[N] Next\n> ")
            if choice == "T":
                utilsy.test_mail(email)
                choice = input(text_input)
            elif choice == "G":
                utilsy.check_google(email, elastic=elastic, password=password)
                choice = input(text_input)
            elif choice == "H":
                utilsy.check_hibp(email, password, elastic=elastic)
                choice = input(text_input)
            elif choice == "P":
                utilsy.check_pipl(email, elastic=elastic, password=password)
                choice = input(text_input)
            elif choice == "F":
                utilsy.check_fullcontact(email, password, elastic=elastic, interactive_flag=True)
                choice = input(text_input)
            elif choice == "I":
                utilsy.send_mail(email, password.rstrip())
                choice = input(text_input)
            elif choice == "N":
                next = True
            else:
                print("Wrong Choice")
