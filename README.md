# Freikatalog

Sammelt einmal am Tag alle freien Filme, Serien und Live-Sender aus den vorhandenen MovieScout-Scrapern und legt sie als fertige Liste ab. Der Scraper `freikatalog.py` liest nur diese Liste: keine Abfragen beim Blättern, Suchen geht sofort. Erst beim Abspielen fragt er den Stream beim jeweiligen Anbieter an.

## So läuft es

1. Der Workflow startet täglich um 03:17 UTC (oder von Hand unter *Actions → Freikatalog → Run workflow*).
2. `sammler/sammeln.py` holt die Scraper aus dem Scraper-Repo und startet jeden in einem eigenen Prozess mit einem Kodi-Ersatz (`sammler/kodi`).
3. Jede Quelle wird nach dem Plan in `sammler/quellen.py` abgelaufen, danach wird alles zusammengeführt. Gleiche Titel aus mehreren Quellen werden zu einem Eintrag mit mehreren Quellen.
4. Das Ergebnis landet im Zweig `daten`, immer als einziger Commit, damit das Repo klein bleibt.

Fällt eine Quelle aus, bleiben ihre alten Einträge bis zu 14 Tage stehen. Der Bericht jedes Laufs steht in der Zusammenfassung des Workflows, die Protokolle liegen 7 Tage als Artefakt bereit.

## Einrichten

1. Neues **öffentliches** Repo anlegen (z. B. `freikatalog`) und diesen Ordner hochladen.
2. *Settings → Actions → General → Workflow permissions*: **Read and write permissions**.
3. Optional unter *Settings → Secrets and variables → Actions*:

| Name | Art | Zweck |
|---|---|---|
| `SCRAPER_REPO` | Variable | Repo mit den Scrapern, Standard `Chrisophy/scraper` |
| `SCRAPER_TOKEN` | Secret | nur nötig, wenn das Scraper-Repo privat ist |
| `KATALOG_PROXY` | Secret | Proxy mit deutscher IP, z. B. `http://user:pass@host:port` |
| `KATALOG_RUNNER` | Variable | `self-hosted`, wenn ein eigener Rechner sammeln soll |

4. Einmal von Hand starten. Danach liegt die Liste unter
   `https://raw.githubusercontent.com/<konto>/<repo>/daten/katalog/index.json`.

Eigene oder geänderte Scraper können zusätzlich in den Ordner `scraper/` gelegt werden, sie haben Vorrang.

## Wichtig: Standort

Die GitHub-Server stehen in den USA. Joyn, RTL+, Netzkino, Pluto, Plex und Rakuten zeigen dort nichts oder ein anderes Angebot. Ohne weitere Einstellung laufen sicher: GEZ KiNO, Kinder-Mediathek, JustWatch (fest auf AT), meist auch TELE 5 und WedoTV. Der Bericht zeigt pro Quelle, ob es geklappt hat.

Zwei Wege für alle Quellen:

- **Eigener Rechner als Runner** (empfohlen): *Settings → Actions → Runners → New self-hosted runner*, Anleitung befolgen, Python 3 muss installiert sein. Dann Variable `KATALOG_RUNNER` = `self-hosted`. Der Rechner muss zur Startzeit an sein.
- **Proxy**: Secret `KATALOG_PROXY` setzen. Er wird nur für die Quellen benutzt, die ihn brauchen.

## Quellen anpassen

`sammler/quellen.py` enthält pro Scraper:

| Feld | Bedeutung |
|---|---|
| `datei` | Dateiname des Scrapers ohne `.py` |
| `prio` | Reihenfolge beim Abspielen, kleiner = zuerst (direkte Links vorne, DRM hinten) |
| `starts` | Einstiege: `art` (`film`, `serie`, `mix`, `live`), `pick` (Menüpunkt aus `load()`), sonst `func` + `url`/`params` |
| `genre_tiefe` | Ordnerebene, deren Titel als Genre gilt |
| `serien_tiefe` | Ordnerebene, deren Ordner Serien sind |
| `nur` | nur diesen Funktionen folgen |
| `max_seiten`, `budget`, `max_aufrufe` | Grenzen gegen zu viele Abfragen |
| `einstellungen` | Werte für `getSetting()` |
| `proxy` | `False` = nie über den Proxy |

Neue Quelle: Eintrag ergänzen, fertig. Scraper, die nicht im Plan stehen, werden übersprungen.

## Lokal testen

```
python3 sammler/sammeln.py --scraper pfad/zu/scrapern --nur plutotv,gezkino --budget-max 120
```

Das Ergebnis liegt dann in `_neu/katalog`, die Protokolle in `_arbeit`.

## Dateien im Zweig `daten`

| Datei | Inhalt |
|---|---|
| `katalog/index.json` | Stand, Bericht pro Quelle, Prüfsummen |
| `katalog/filme.json.gz` | alle Filme |
| `katalog/serien.json.gz` | alle Serien |
| `katalog/live.json.gz` | alle Live-Sender |
| `katalog/erstmals.json.gz` | wann ein Titel zuerst auftauchte (für „Neu“) |
| `katalog/quellen/*.json.gz` | Rohdaten pro Quelle |

Es werden nur Titel, Bilder, Beschreibungen und die Kennungen der Anbieter gespeichert, keine Tokens und keine Stream-Adressen mit Ablaufdatum.

## Hinweis

GitHub schaltet geplante Workflows in öffentlichen Repos nach 60 Tagen ohne Aktivität ab. Dann unter *Actions* einmal wieder aktivieren.
