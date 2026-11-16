"""Fils automatiques : un fil pour chaque message de certains salons.

Demande de Romain (Pause IA, 02/11/2026) : dans les salons de discussion
générale (« bavardages », « actualité »), créer un fil pour chaque nouveau
message, pour inciter à répondre dans le fil plutôt qu'en vrac dans le salon.

Les salons concernés sont listés par identifiant dans la configuration
(`discord.auto_thread_channels`). Liste vide = fonctionnalité désactivée.

Fonctions pures, sans appel à Discord, pour pouvoir les tester seules : le bot
(bot.py) décide quand les appeler et crée le fil.
"""
import re

from Modules import strings

THREAD_NAME_LIMIT = 100  # limite imposée par Discord

_URL = re.compile(r"https?://\S+")
_MARKDOWN = re.compile(r"[*_~`>|#]+")
_ESPACES = re.compile(r"\s+")
_SITE = re.compile(r"https?://(?:www\.)?([^/?#\s:]+)", re.IGNORECASE)


def should_auto_thread(channel_id, auto_channel_ids, author_is_bot,
                       is_regular_message, content, command_prefix):
    """Faut-il créer un fil pour ce message ?

    Non pour : un salon hors liste ; un bot (Hal compris : il ne doit pas
    répondre à ses propres messages ni à ceux des autres bots) ; un message
    système (épinglage, arrivée d'un membre, annonce de fil…) ; une commande
    du bot (« !pia … »).
    """
    if channel_id not in auto_channel_ids:
        return False
    if author_is_bot or not is_regular_message:
        return False
    if command_prefix and (content or "").lstrip().startswith(command_prefix):
        return False
    return True


def _raccourcir(nom):
    if len(nom) > THREAD_NAME_LIMIT:
        coupe = nom[:THREAD_NAME_LIMIT - 1]
        # Couper sur un espace plutôt qu'au milieu d'un mot, si possible.
        espace = coupe.rfind(" ")
        if espace > THREAD_NAME_LIMIT // 2:
            coupe = coupe[:espace]
        nom = coupe.rstrip(" ,;:.-") + "…"
    return nom


def _nettoyer(texte):
    texte = _MARKDOWN.sub("", texte or "")
    return _ESPACES.sub(" ", texte).strip()


def embed_title(embeds):
    """Le titre de l'aperçu que Discord affiche sous un lien (balise og:title
    de la page), ou "" s'il n'y en a pas encore.

    Discord ajoute souvent cet aperçu quelques secondes APRÈS l'envoi du
    message : le bot le reçoit alors comme une modification du message
    (voir `on_message_edit` dans bot.py).
    """
    for embed in embeds or []:
        titre = _nettoyer(getattr(embed, "title", None) or "")
        if titre:
            return titre
    return ""


def thread_name_from_message(content, author_name, link_title=""):
    """Le nom du fil : la première ligne du message, nettoyée et raccourcie.

    Les liens deviennent « lien », la mise en forme Markdown est retirée.
    Demande de Jeanne (11/11/2026) : un message qui n'est qu'un lien prend le
    titre de la page partagée (`link_title`, voir `embed_title`) ; tant que ce
    titre n'est pas connu, le nom du site (« lemonde.fr »). Un message sans
    texte ni lien (image seule, par exemple) donne un nom générique avec
    l'auteur·ice.
    """
    premiere = next((ligne for ligne in (content or "").splitlines()
                     if ligne.strip()), "")
    nom = _nettoyer(_URL.sub("lien", premiere))
    if not nom or nom == "lien":
        lien = _URL.search(content or "")
        site = _SITE.match(lien.group(0)) if lien else None
        if link_title:
            nom = _nettoyer(link_title)
        elif site:
            nom = site.group(1).lower()
        else:
            nom = strings.AUTO_THREAD_DEFAULT_NAME.format(author=author_name or "?")
    return _raccourcir(nom)
