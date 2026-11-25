# -*- coding: utf-8 -*-
# zusatzmetall | IT('s) Possible
# 2026.11.25

DE_IP = '91.12.34.56'
DEUTSCHLAND = {'X-Forwarded-For': DE_IP}

PLEX_SUCHE = [
    'der', 'die', 'the', 'das', 'und', 'des', 'ein', 'auf', 'von', 'liebe', 'mit', 'teil', 'für', 'eine', 'ist',
    'folge', 'den', 'leben', 'dem', 'zum', 'mein', 'weihnachten', 'nicht', 'aus', 'ich', 'man', 'love', 'nach',
    'tod', 'christmas', 'glück', 'wir', 'war', 'geschichte', 'and', 'meine', 'mann', 'kleine', 'welt', 'zwei',
    'alles', 'letzte', 'vom', 'hölle', 'rache', 'weltkrieg', 'geheimnis', 'wie', 'unter', 'gegen', 'familie',
    'for', 'reich', 'immer', 'nacht', 'night', 'abenteuer', 'einer', 'episode', 'last', 'frauen', 'zur', 'kampf',
    'dark', 'world', 'drei', 'große', 'time', 'all', 'alle', 'was', 'sie', 'vier', 'krieg', 'frau', 'berlin',
    'missions', 'tödliche', 'sex', 'staffel', 'schlacht', 'oder', 'freund', 'reise', 'kein', 'bis', 'sind', 'ins',
    'life', 'monster', 'dead', 'mord', 'ohne', 'kommt', 'dich', 'nur', 'new', 'lebens', 'zurück', 'legende',
    'kinder', 'fall', 'dein', 'killer', 'shaolin', 'spione', 'agenten', 'red', 'story', 'hochzeit', 'weg', 'you',
    'sein', 'herz', 'soldaten', 'deutschland', 'verlieben', 'wild', 'inside', 'erde', 'tage', 'durch', 'zeit',
    'als', 'american', 'evil', 'tag', 'verliebt', 'zweite', 'shark', 'zwischen', 'dir', 'city', 'bei', 'wer',
    'über', 'allein', 'house', 'deutsche', 'ende', 'traum', 'mutter', 'king', 'macht', 'wenn', 'west', 'death',
    'haus', 'weihnachtsmann', 'spiel', 'bösen', 'star', 'mission', 'sommer', 'noch', 'männer', 'schatten', 'jagd',
    'kann', 'mädchen', 'vor', 'andere', 'vater', 'keine', 'blood', 'big', 'gold', 'battle', 'tochter', 'himmel',
    'eines', 'ihr', 'black', 'one', 'bvb', 'fast', 'engel', 'girls', 'hat', 'geht', 'herzen', 'einen', 'wieder',
    'terror', 'land', 'unser', 'uns', 'girl', 'tiger', 'mary', 'papa', 'leidenschaft', 'jahre', 'from',
    'traktoren', 'wunder', 'angst', 'hitler', 'island', 'mich', 'könig', 'wird', 'hitlers', 'zweiten', 'winnetou',
    'with', 'freiheit', 'earth', 'agatha', 'christie', 'alien', 'road', 'tiefe', 'insel', 'vergangenheit',
    'gesetz', 'park', 'wahrheit', 'bruce', 'operation', 'europa', 'django', 'winter', 'high', 'just', 'mom',
    'zombie', 'days', 'letzten', 'dog', 'freunde', 'river', 'weißen', 'voll', 'morde', 'bin', 'giganten', 'york',
    'einem', 'gestern', 'animal', 'wilden', 'angriff', 'mir', 'wahre', 'end', 'lee', 'todes', 'china', 'erste',
    'einsatz', 'lady', 'evolution', 'serie', 'saison', 'seine', 'suche', 'afrika', 'devil', 'anfang', 'sonne',
    'poltergeist', 'animals', 'wilde', 'spur', 'einmal', 'überleben', 'beast', 'meiner', 'kill', 'drachen',
    'race', 'first', 'max', 'regionalliga', 'spieltag', 'tiere', 'bull', 'apocalypse', 'boy', 'hoffnung',
    'spuren', 'zombies', 'lügen', 'ganz', 'cop', 'augen', 'killers', 'art', 'untergang', 'day', 'wars', 'baby',
    'bescherung', 'plötzlich', 'zukunft', 'gibt', 'freundschaft', 'super', 'ferien', 'good', 'white', 'little',
    'clark', 'teen', 'nie', 'attack', 'deine', 'heart', 'legend', 'santa', 'chance', 'kind', 'stadt', 'ärger',
    'see', 'neue', 'amazing', 'sieben', 'horror'
]

ALLGEMEIN = {
    'parallel': 4,
    'budget': 900,
    'max_aufrufe': 1500,
    'tiefe': 3,
    'max_seiten': 40,
    'pause': 0.1,
    'plot_laenge': 400,
    'alt_tage': 14,
}

QUELLEN = [
    {
        'datei': 'gezkino',
        'prio': 10,
        'proxy': False,
        'starts': [
            {'art': 'film', 'roh': 'gez'},
        ],
    },
    {
        'datei': 'kindermediathek',
        'prio': 12,
        'proxy': False,
        'direkt': 'kmt',
        'starts': [
            {'art': 'film', 'pick': 'Filme', 'func': 'load', 'params': {'lvl': 'films'}, 'genre': 'Kinder', 'alle_abspielbar': True},
            {'art': 'serie', 'pick': 'Sendungen A–Z', 'func': 'load', 'params': {'lvl': 'shows'}, 'serien_tiefe': 1, 'genre': 'Kinder'},
        ],
    },
    {
        'datei': 'netzkino',
        'prio': 20,
        'budget': 2400,
        'max_aufrufe': 2500,
        'starts': [
            {'art': 'film', 'pick': 'Alle Filme A - Z', 'func': 'showEntries', 'url': 'alle-filme', 'max_seiten': 200},
            {'art': 'film', 'pick': 'Genres', 'func': 'showGenres', 'genre_tiefe': 1, 'nur': ['showEntries'], 'max_seiten': 60},
            {'art': 'serie', 'pick': 'Serien', 'func': 'showEntries', 'url': 'serien'},
        ],
    },
    {
        'datei': 'wedotv',
        'prio': 30,
        'starts': [
            {'art': 'film', 'pick': 'Filme', 'func': 'showMovieGenres', 'genre_tiefe': 1, 'nur': ['showGenreMovies']},
            {'art': 'serie', 'pick': 'Serien', 'func': 'showSeries', 'genre_tiefe': 1, 'nur': ['showSeriesGenre']},
        ],
    },
    {
        'datei': 'plutotv',
        'prio': 40,
        'kopfzeilen': DEUTSCHLAND,
        'starts': [
            {'art': 'film', 'func': '_rest_genres', 'args': ['movie'], 'genre_tiefe': 1,
             'alt': {'pick': 'Filme', 'func': 'showGenres', 'url': 'movies', 'genre_tiefe': 1}},
            {'art': 'serie', 'func': '_rest_genres', 'args': ['show'], 'genre_tiefe': 1,
             'alt': {'pick': 'Serien', 'func': 'showGenres', 'url': 'shows', 'genre_tiefe': 1}},
            {'art': 'live', 'func': 'get_live_channels', 'url': 'channels:de:__all__',
             'alt': {'pick': 'Live TV', 'func': 'get_live', 'url': 'live'}},
        ],
    },
    {
        'datei': 'rakutentv',
        'prio': 45,
        'starts': [
            {'art': 'film', 'pick': 'Filme', 'func': 'showGenres', 'url': 'free-movies', 'genre_tiefe': 1},
            {'art': 'serie', 'pick': 'Serien', 'func': 'showGenres', 'url': 'free-shows', 'genre_tiefe': 1},
            {'art': 'live', 'pick': 'Live TV (alle Kanäle)', 'func': 'showAllLiveChannels', 'url': 'all'},
        ],
    },
    {
        'datei': 'plexfree',
        'prio': 50,
        'budget': 2400,
        'max_aufrufe': 1000,
        'kopfzeilen': DEUTSCHLAND,
        'einstellungen': {'general.german_only': 'true'},
        'starts': [
            {'art': 'mix', 'pick': 'Entdecken & Kategorien', 'func': 'load', 'url': 'hubs', 'genre_tiefe': 1, 'max_seiten': 15},
            {'art': 'mix', 'roh': 'plex', 'suche': PLEX_SUCHE},
            {'art': 'live', 'pick': 'Live TV - Deutsch', 'func': 'load', 'url': 'live_de'},
        ],
    },
    {
        'datei': 'rtlfree',
        'prio': 60,
        'starts': [
            {'art': 'film', 'pick': 'Filme'},
            {'art': 'serie', 'pick': 'Serien'},
            {'art': 'live', 'pick': 'Live TV', 'func': 'get_live'},
        ],
    },
    {
        'datei': 'joynfree',
        'prio': 70,
        'starts': [
            {'art': 'film', 'pick': 'Alle Filme', 'func': 'showEntries', 'url': 'menu:all_movies', 'max_seiten': 120},
            {'art': 'serie', 'pick': 'TV-Serien', 'func': 'showEntries', 'url': 'cat:/serien'},
            {'art': 'live', 'pick': 'Live TV', 'func': 'get_live', 'url': 'menu:live'},
        ],
    },
    {
        'datei': 'justwatch',
        'prio': 80,
        'proxy': False,
        'starts': [
            {'art': 'film', 'pick': 'Filme', 'func': 'showEntries', 'url': 'movies', 'max_seiten': 80},
            {'art': 'serie', 'pick': 'Serien', 'func': 'showEntries', 'url': 'series', 'max_seiten': 80},
        ],
    },
]
