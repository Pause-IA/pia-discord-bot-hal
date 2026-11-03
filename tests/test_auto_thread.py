"""Fils automatiques dans les salons de discussion (bavardages, actualité).

Lancer depuis la racine du dépôt :  python -m unittest discover -s tests
"""
import os
import sys
import unittest
from types import SimpleNamespace
from unittest import mock

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)

import discord  # noqa: E402

from Modules.Discord import auto_thread  # noqa: E402
from Modules.Discord.bot import PiaBot  # noqa: E402

BAVARDAGES, ACTUALITE, VIDEOS, AUTRE = 111, 222, 333, 444


class Regles(unittest.TestCase):
    def ok(self, **kw):
        args = dict(channel_id=BAVARDAGES, auto_channel_ids=[BAVARDAGES],
                    author_is_bot=False, is_regular_message=True,
                    content="Bonjour à tous", command_prefix="!pia")
        args.update(kw)
        return auto_thread.should_auto_thread(**args)

    def test_message_ordinaire(self):
        self.assertTrue(self.ok())

    def test_salon_hors_liste(self):
        self.assertFalse(self.ok(channel_id=AUTRE))

    def test_liste_vide_desactive_tout(self):
        self.assertFalse(self.ok(auto_channel_ids=[]))

    def test_bot_ignore(self):
        self.assertFalse(self.ok(author_is_bot=True))

    def test_message_systeme_ignore(self):
        self.assertFalse(self.ok(is_regular_message=False))

    def test_commande_ignoree(self):
        self.assertFalse(self.ok(content="  !pia queue"))


class NomDuFil(unittest.TestCase):
    def test_premiere_ligne(self):
        self.assertEqual(auto_thread.thread_name_from_message(
            "Article intéressant\nsur la régulation", "Antoine"), "Article intéressant")

    def test_liens_et_markdown(self):
        self.assertEqual(auto_thread.thread_name_from_message(
            "**À lire** : https://exemple.org/article?x=1 _vite_", "Antoine"),
            "À lire : lien vite")

    def test_lien_seul_ou_image_seule(self):
        self.assertEqual(auto_thread.thread_name_from_message(
            "https://exemple.org/a", "Antoine"), "Discussion de Antoine")
        self.assertEqual(auto_thread.thread_name_from_message("", "Antoine"),
                         "Discussion de Antoine")

    def test_cent_caracteres_au_plus_coupe_sur_un_mot(self):
        nom = auto_thread.thread_name_from_message("mot " * 60, "Antoine")
        self.assertLessEqual(len(nom), auto_thread.THREAD_NAME_LIMIT)
        self.assertTrue(nom.endswith("mot…"), nom)


def faux_message(channel_id, content="Bonjour à tous", bot=False,
                 type_=discord.MessageType.default):
    msg = mock.MagicMock()
    msg.channel = SimpleNamespace(id=channel_id)
    msg.content = content
    msg.clean_content = content
    msg.author = SimpleNamespace(bot=bot, display_name="Antoine")
    msg.type = type_
    msg.id = 1
    msg.create_thread = mock.AsyncMock()
    return msg


class DansLeBot(unittest.IsolatedAsyncioTestCase):
    """on_message, sans connexion à Discord."""

    def setUp(self):
        self.bot = PiaBot.__new__(PiaBot)  # sans __init__ : pas de config ni de réseau
        self.bot.monitored_channel_ids = [VIDEOS, BAVARDAGES]
        self.bot.auto_thread_channel_ids = [BAVARDAGES, ACTUALITE]
        self.bot.command_prefix = "!pia"
        self.bot.process_commands = mock.AsyncMock()
        self.bot._process_url = mock.AsyncMock()
        self.bot._is_supported_url = mock.AsyncMock(
            side_effect=lambda url: "youtube.com" in url)
        patcher = mock.patch.object(PiaBot, "user", new_callable=mock.PropertyMock,
                                    return_value=object())
        patcher.start()
        self.addCleanup(patcher.stop)

    async def test_un_fil_par_message_dans_actualite(self):
        msg = faux_message(ACTUALITE, "Nouvelle loi sur l'IA")
        await self.bot.on_message(msg)
        msg.create_thread.assert_awaited_once_with(name="Nouvelle loi sur l'IA")

    async def test_rien_ailleurs(self):
        msg = faux_message(AUTRE)
        await self.bot.on_message(msg)
        msg.create_thread.assert_not_awaited()

    async def test_video_un_seul_fil_celui_du_resume(self):
        # Salon à la fois surveillé et à fils automatiques : Hal crée déjà le
        # fil du résumé, pas question d'en créer un second.
        msg = faux_message(BAVARDAGES, "Regardez https://www.youtube.com/watch?v=abc")
        await self.bot.on_message(msg)
        msg.create_thread.assert_not_awaited()
        self.bot._process_url.assert_awaited_once()

    async def test_lien_non_video_reste_un_fil_automatique(self):
        msg = faux_message(BAVARDAGES, "Article : https://exemple.org/a")
        await self.bot.on_message(msg)
        msg.create_thread.assert_awaited_once()
        self.bot._process_url.assert_not_awaited()

    async def test_video_hors_salon_a_fils_inchange(self):
        msg = faux_message(VIDEOS, "https://youtu.be/x https://www.youtube.com/watch?v=abc")
        await self.bot.on_message(msg)
        msg.create_thread.assert_not_awaited()
        self.bot._process_url.assert_awaited_once()

    async def test_un_refus_de_discord_ne_fait_pas_tomber_le_bot(self):
        msg = faux_message(ACTUALITE)
        msg.create_thread.side_effect = discord.Forbidden(
            mock.MagicMock(status=403, reason="Forbidden"), "Missing Permissions")
        with self.assertLogs("Modules.Discord.bot", level="WARNING"):
            await self.bot.on_message(msg)

    async def test_bot_et_message_systeme_ignores(self):
        for msg in (faux_message(ACTUALITE, bot=True),
                    faux_message(ACTUALITE, type_=discord.MessageType.pins_add)):
            await self.bot.on_message(msg)
            msg.create_thread.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
