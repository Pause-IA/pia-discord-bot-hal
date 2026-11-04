"""Le résumé par Claude doit appeler le SDK anthropic avec des paramètres qu'il accepte.

Le 04/11/2026, après la reconstruction de l'image (pip a installé anthropic 2.x),
chaque résumé échouait : « AsyncMessages.create() got an unexpected keyword
argument 'temperature' ». Ce test confronte l'appel à la vraie signature du SDK
installé, sans réseau ni clé.

Lancer depuis la racine du dépôt :  python -m unittest discover -s tests
"""
import inspect
import os
import sys
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest import mock

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)

import anthropic  # noqa: E402

from Modules.Commons import ContentItem  # noqa: E402
from Modules.Summarization import claude  # noqa: E402

SIGNATURE = inspect.signature(anthropic.resources.messages.AsyncMessages.create)


async def faux_create(**kwargs):
    # Lève TypeError, comme le vrai SDK, si un paramètre n'existe pas.
    SIGNATURE.bind(None, **kwargs)
    texte = '{"summary": "Un résumé en français.", "tags": ["IA"]}'
    return SimpleNamespace(content=[SimpleNamespace(text=texte)])


class ResumeClaude(unittest.IsolatedAsyncioTestCase):
    async def test_appel_accepte_par_le_sdk_installe(self):
        client = SimpleNamespace(messages=SimpleNamespace(
            create=mock.AsyncMock(side_effect=faux_create)))
        reglages = SimpleNamespace(api_key="x", model="claude-test")
        item = ContentItem(type="youtube", content_id="abc", url="https://youtu.be/abc",
                           title="Titre", author="Auteur", date=datetime(2026, 11, 4),
                           content="Transcription.")
        with mock.patch.object(claude.anthropic, "AsyncAnthropic", return_value=client), \
                mock.patch.object(claude.config, "get_summarization", return_value=reglages):
            resume = await claude.summarize_with_claude(item)
        self.assertEqual(resume.summary, "Un résumé en français.")
        self.assertEqual(resume.tags, ["IA"])


if __name__ == "__main__":
    unittest.main()
