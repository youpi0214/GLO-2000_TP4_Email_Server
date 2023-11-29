"""\
GLO-2000 Travail pratique 4 - Serveur
Noms et numéros étudiants:
-
-
-
"""

import hashlib
import hmac
import json
import os
import select
import socket
import sys

import glosocket
import gloutils
from gloutils import *
from glosocket import *


class Server:
    """Serveur mail @glo2000.ca."""

    def __init__(self) -> None:
        """
        Prépare le socket du serveur `_server_socket`
        et le met en mode écoute.

        Prépare les attributs suivants:
        - `_client_socs` une liste des sockets clients.
        - `_logged_users` un dictionnaire associant chaque
            socket client à un nom d'utilisateur.

        S'assure que les dossiers de données du serveur existent.
        """
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(("127.0.0.1", gloutils.APP_PORT))
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.listen()
        self._client_socs = []
        self._logged_users = {}

    def cleanup(self) -> None:
        """Ferme toutes les connexions résiduelles."""
        for client_soc in self._client_socs:
            self._remove_client(client_soc)
        self._server_socket.close()

    def _accept_client(self) -> None:
        """Accepte un nouveau client."""
        client_soc, _ = self._server_socket.accept()
        self._client_socs.append(client_soc)
        print("new Connection! now,", len(self._client_socs), "clients connected")

    def _remove_client(self, client_soc: socket.socket) -> None:
        """Retire le client des structures de données et ferme sa connexion."""
        client_soc.close()
        self._client_socs.remove(client_soc)
        self._logged_users.pop(client_soc, None)

    def _create_account(self, client_soc: socket.socket,
                        payload: gloutils.AuthPayload
                        ) -> gloutils.GloMessage:
        """
        Crée un compte à partir des données du payload.

        Si les identifiants sont valides, créee le dossier de l'utilisateur,
        associe le socket au nouvel l'utilisateur et retourne un succès,
        sinon retourne un message d'erreur.
        """
        username = payload['username']
        password = payload['password']
        user_dir = os.path.join(gloutils.SERVER_DATA_DIR, username)

        if os.path.exists(user_dir):
            error_message = "La création a échouée:\n\t- Le nom d'utilisateur est invalide.\n\t- Le mot de passe n'est pas assez sûr."
            error_payload: ErrorPayload = {"error_message": error_message}
            message: GloMessage = GloMessage({"header": Headers.ERROR, "payload": error_payload})
            send_mesg(client_soc, json.dumps(message))
        else:
            os.makedirs(user_dir)

            # Stockage sécurisé du mot de passe
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            with open(os.path.join(user_dir, PASSWORD_FILENAME), 'w') as f:
                f.write(hashed_password)

            self._logged_users[client_soc] = username
            message: GloMessage = GloMessage({"header": Headers.OK})
            send_mesg(client_soc, json.dumps(message))

    def _login(self, client_soc: socket.socket, payload: gloutils.AuthPayload) -> gloutils.GloMessage:
        """
        Vérifie que les données fournies correspondent à un compte existant.

        Si les identifiants sont valides, associe le socket à l'utilisateur et
        retourne un succès, sinon retourne un message d'erreur.
        """
        username = payload['username']
        password = payload['password']
        user_dir = os.path.join(gloutils.SERVER_DATA_DIR, username)

        authenticated = False
        if os.path.exists(user_dir):
            with open(os.path.join(user_dir, PASSWORD_FILENAME), 'r') as f:
                stored_password = f.read()
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            if hashed_password == stored_password:
                authenticated = True
                message: GloMessage = GloMessage({"header": Headers.OK})
                send_mesg(client_soc, json.dumps(message))

        if not authenticated:
            error_message = "Nom d'utilisateur ou mot de passe invalide."
            error_payload: ErrorPayload = {"error_message": error_message}
            message: GloMessage = GloMessage({"header": Headers.ERROR, "payload": error_payload})
            send_mesg(client_soc, json.dumps(message))


        self._logged_users[client_soc] = username

    def _logout(self, client_soc: socket.socket) -> None:
        """Déconnecte un utilisateur."""

    def _get_email_list(self, client_soc: socket.socket) -> gloutils.GloMessage:
        """
        Récupère la liste des courriels de l'utilisateur associé au socket.
        Les éléments de la liste sont construits à l'aide du gabarit
        SUBJECT_DISPLAY et sont ordonnés du plus récent au plus ancien.

        Une absence de courriel n'est pas une erreur, mais une liste vide.
        """
        return gloutils.GloMessage()

    def _get_email(self, client_soc: socket.socket,
                   payload: gloutils.EmailChoicePayload) -> gloutils.GloMessage:
        """
        Récupère le contenu de l'email dans le dossier de l'utilisateur associé
        au socket.
        """
        return gloutils.GloMessage()

    def _get_stats(self, client_soc: socket.socket) -> gloutils.GloMessage:
        """
        Récupère le nombre de courriels et la taille du dossier et des fichiers
        de l'utilisateur associé au socket.
        """
        return gloutils.GloMessage()

    def _send_email(self, payload: gloutils.EmailContentPayload) -> gloutils.GloMessage:
        """
        Détermine si l'envoi est interne ou externe et:
        - Si l'envoi est interne, écris le message tel quel dans le dossier
        du destinataire.
        - Si le destinataire n'existe pas, place le message dans le dossier
        SERVER_LOST_DIR et considère l'envoi comme un échec.
        - Si le destinataire est externe, considère l'envoi comme un échec.

        Retourne un messange indiquant le succès ou l'échec de l'opération.
        """
        return gloutils.GloMessage()

    def run(self):
        """Point d'entrée du serveur."""

        print("server starts")
        while True:
            waiters, _, _ = select.select([self._server_socket] + self._client_socs, [], [])

            # Select readable sockets
            for waiter in waiters:
                # Handle sockets
                if waiter is self._server_socket:
                    # ... Handle new connection
                    self._accept_client()
                else:
                    # ... Handle existing connection
                    try:
                        data = glosocket.recv_mesg(waiter)
                    except glosocket.GLOSocketError:
                        self._remove_client(waiter)
                        continue

                    match json.loads(data):
                        case {"header": Headers.AUTH_REGISTER, "payload": payload}:
                            self._create_account(waiter, payload)
                        case {"header": Headers.AUTH_LOGIN, "payload": payload}:
                            self._login(waiter, payload)
                        case {"header": Headers.AUTH_LOGOUT}:
                            self._logout(waiter)
                        case {"header": Headers.INBOX_READING_CHOICE, "payload": payload}:
                            self._get_email(waiter, payload)
                        case {"header": Headers.INBOX_READING_REQUEST}:
                            self._get_email_list(waiter, payload)
                        case {"header": Headers.EMAIL_SENDING}:
                            self._send_email(waiter, payload)
                        case {"header": Headers.STATS_REQUEST}:
                            self._get_stats(waiter)


def _main() -> int:
    server = Server()
    try:
        server.run()
    except KeyboardInterrupt:
        server.cleanup()
    return 0


if __name__ == '__main__':
    sys.exit(_main())
