"""Language settings shared by render.py and publish.py, read from ../languages.json.

The first enabled language is the main one: its files keep the plain names (<base>.md, <base>.html)
and it is published at reports/<base>/. Every other language uses <base>.<code>.md / .html and is
published at reports/<base>/<code>/.
"""
import datetime, json, os

CONFIG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "languages.json")


def load():
    """Enabled languages in config order; the first is the main language."""
    langs = [l for l in json.load(open(CONFIG, encoding="utf-8"))["languages"] if l.get("enabled", True)]
    if not langs:
        raise SystemExit(f"no enabled languages in {CONFIG}")
    return langs


def main_lang(langs):
    return langs[0]


def suffix(lang, langs):
    """'' for the main language, '.<code>' for the others (used in <base><suffix>.md)."""
    return "" if lang is main_lang(langs) else "." + lang["code"]


def split_name(stem, langs):
    """Split a file stem like '<base>.zh-hans' into (base, lang); a stem without a known code is main."""
    for lang in langs[1:]:
        if stem.endswith("." + lang["code"]):
            return stem[: -len(lang["code"]) - 1], lang
    return stem, main_lang(langs)


def format_date(d: datetime.date, lang):
    months = lang.get("months") or [str(m) for m in range(1, 13)]
    return lang["date_format"].format(year=d.year, month=d.month, day=d.day,
                                      month_abbr=months[d.month - 1], month_name=months[d.month - 1])
