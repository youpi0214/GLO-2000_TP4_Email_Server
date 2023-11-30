"""\
GLO-2000 Travail pratique 4 - Client
Noms et numéros étudiants:
-
-
-
"""

import argparse
import getpass
import json
import socket
import sys

import glosocket
import gloutils
from gloutils import *
from glosocket import *


class Client:
    """Client pour le serveur mail @glo2000.ca."""

    def __init__(self, destination: str) -> None:
        """
        Prépare et connecte le socket du client `_socket`.

        Prépare un attribut `_username` pour stocker le nom d'utilisateur
        courant. Laissé vide quand l'utilisateur n'est pas connecté.
        """
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((destination, gloutils.APP_PORT))
        self._username = ""

    def _register(self) -> None:
        """
        Demande un nom d'utilisateur et un mot de passe et les transmet au
        serveur avec l'entête `AUTH_REGISTER`.

        Si la création du compte s'est effectuée avec succès, l'attribut
        `_username` est mis à jour, sinon l'erreur est affichée.
        """
        username = input("Nom d'utilisateur : ")
        password = getpass.getpass("Mot de passe : ")

        # Envoi de la requête d'inscription
        auth_payload: AuthPayload = AuthPayload(username=username, password=password)
        message: GloMessage = GloMessage(header=Headers.AUTH_REGISTER, payload=auth_payload)
        send_mesg(self._socket, json.dumps(message))

        # Réception de la réponse
        response = recv_mesg(self._socket)
        match json.loads(response):
            case {"header": Headers.OK}:
                self._username = username
            case {"header": Headers.ERROR, "payload": payload}:
                print(payload["error_message"])

    def _login(self) -> None:
        """
        Demande un nom d'utilisateur et un mot de passe et les transmet au
        serveur avec l'entête `AUTH_LOGIN`.

        Si la connexion est effectuée avec succès, l'attribut `_username`
        est mis à jour, sinon l'erreur est affichée.
        """

        username = input("Nom d'utilisateur : ")
        password = getpass.getpass("Mot de passe : ")

        # Preparation et envoi de la requête de connexion
        auth_payload: AuthPayload = AuthPayload(username=username, password=password)
        message: GloMessage = GloMessage(header=Headers.AUTH_LOGIN, payload=auth_payload)
        send_mesg(self._socket, json.dumps(message))

        # Réception de la réponse
        response = glosocket.recv_mesg(self._socket)
        match json.loads(response):
            case {"header": Headers.OK}:
                self._username = username
            case {"header": Headers.ERROR, "payload": payload}:
                print(payload["error_message"])

    def _quit(self) -> None:
        """
        Préviens le serveur de la déconnexion avec l'entête `BYE` et ferme le
        socket du client.
        """
        self._socket.send(gloutils.BYE, {"username": self._username})
        self._socket.close()

    def _read_email(self) -> None:
        """
        Demande au serveur la liste de ses courriels avec l'entête
        `INBOX_READING_REQUEST`.

        Affiche la liste des courriels puis transmet le choix de l'utilisateur
        avec l'entête `INBOX_READING_CHOICE`.

        Affiche le courriel à l'aide du gabarit `EMAIL_DISPLAY`.

        S'il n'y a pas de courriel à lire, l'utilisateur est averti avant de
        retourner au menu principal.
        """
        # Preparation et envoi de la requête de demande de liste de courriel
        message: GloMessage = GloMessage(header=Headers.INBOX_READING_REQUEST)
        send_mesg(self._socket, json.dumps(message))

        # Réception de la liste des courriels
        response = recv_mesg(self._socket)
        match json.loads(response):
            case {"header": Headers.INBOX_READING_REQUEST, "payload": payload}:
                email_list = payload["email_list"]
                if not email_list:
                    print("Aucun courriel à lire.")
                else:
                    for email in email_list:
                        print(email)
                    choice = int(input(f"Entrez votre choix [1-{len(email_list)}]: "))

                    # Preparation et envoi de la requête de demande de lecture de courriel
                    choice_payload = EmailChoicePayload(choice=choice)
                    message: GloMessage = GloMessage(header=Headers.INBOX_READING_CHOICE, payload=choice_payload)
                    send_mesg(self._socket, json.dumps(message))

    def _send_email(self) -> None:
        """
        Demande à l'utilisateur respectivement:
        - l'adresse email du destinataire,
        - le sujet du message,
        - le corps du message.

        La saisie du corps se termine par un point seul sur une ligne.

        Transmet ces informations avec l'entête `EMAIL_SENDING`.
        """
        # Récupération des données pour les champs du courriel
        mail_to: str = input("Entrez l'adresse du destinataire: ")
        subject: str = input("Entrez le sujet: ")
        print("Entrez le contenu du courriel, terminez la saisie avec un '.' seul sur une ligne:")
        content = ""
        buffer = ""
        while (buffer != ".\n"):
            content += buffer
            buffer = input() + '\n'

        email_payload: EmailContentPayload = EmailContentPayload(sender=f"{self._username}@{SERVER_DOMAIN}",
                                                                 destination=mail_to, subject=subject,
                                                                 date=get_current_utc_time(), content=content)
        message: GloMessage = GloMessage(header=Headers.EMAIL_SENDING, payload=email_payload)
        send_mesg(self._socket, json.dumps(message))

        response = recv_mesg(self._socket)
        match json.loads(response):
            case {"header": Headers.OK}:
                pass
            case {"header": Headers.ERROR, "payload": payload}:
                print(payload["error_message"])

    def _check_stats(self) -> None:
        """
        Demande les statistiques au serveur avec l'entête `STATS_REQUEST`.

        Affiche les statistiques à l'aide du gabarit `STATS_DISPLAY`.
        """

    def _logout(self) -> None:
        """
        Préviens le serveur avec l'entête `AUTH_LOGOUT`.

        Met à jour l'attribut `_username`.
        """

    def run(self) -> None:
        """Point d'entrée du client."""
        should_quit = False

        while not should_quit:
            if not self._username:
                # Authentication menu
                try:
                    option = int(input(CLIENT_AUTH_CHOICE + "\nEntrez votre choix [1-3]: "))
                    if not (1 <= option <= 3):
                        raise ValueError()
                    else:
                        if option == 1:
                            self._register()
                        elif option == 2:
                            self._login()
                        elif option == 3:
                            self._quit()
                            should_quit = True
                except ValueError:
                    print("Rentrez une valeur dans l\'intervale demandé...")

            else:
                try:
                    option = int(input(CLIENT_USE_CHOICE + "\nEntrez votre choix [1-4]: "))
                    if not (1 <= option <= 4):
                        raise ValueError()
                    else:
                        if option == 1:
                            self._read_email()
                        elif option == 2:
                            self._send_email()
                        elif option == 3:
                            self._check_stats()
                        elif option == 4:
                            self._logout()
                except ValueError:
                    print("Rentrez une valeur dans l\'intervale demandé...")


def _main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--destination", action="store",
                        dest="dest", required=True,
                        help="Adresse IP/URL du serveur.")
    args = parser.parse_args(sys.argv[1:])
    client = Client(args.dest)
    client.run()
    return 0


if __name__ == '__main__':
    sys.exit(_main())
