from __future__ import annotations


# Dictionary of idioms and colloquial expressions.
# Here we store contextual translations for each target language.
#
# Format:
# "source_phrase": {
#     "en": "natural English",
#     "fi": "luonteva suomi",
# }

IDIOMS: dict[str, dict[str, str]] = {
    "вот такие пироги": {
        "en": "that's how it is",
        "fi": "sellaista se on",
    },
    "ничего себе": {
        "en": "wow",
        "fi": "oho",
    },
    "да ну": {
        "en": "no way",
        "fi": "ei voi olla",
    },
    "ну да": {
        "en": "yeah, right",
        "fi": "niinpä",
    },
}