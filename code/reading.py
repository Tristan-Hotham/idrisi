"""Hand decisions, made by reading the sources.

ROUTES: al-Idrisi's own distances between places, read in Dozy and de Goeje's French translation (1866) and checked
line by line against the scan's text. Each entry: (from, to, miles, days, OCR line, words quoted from the OCR line).
  * miles: the distance in Arab miles where the text gives one; days: in day stages (journees, Arabic marhala) where it
    gives one. Some routes give both.
  * Only distances between two places I can identify with confidence today, over land or along a coast (not by sea),
    are used. Where the OCR misreads a number I give the number the context requires and say so (Mequinenza to Tortosa:
    'SO' is 50).
EXTRA: coordinates for places in ROUTES that are not among the places I located on the map.
"""

ROUTES = [
    # North Africa, miles
    ("Fez", "Meknes", 40, None, 5062, "De  Fèz  à Mecnâsa  (Méquinèz)  , on  compte  40  milles"),
    ("Aghmat", "Marrakesh", 12, None, 4623, "Au  nord  d'Aghmât , à la  distance  de  1 2 milles , est  Maroc"),
    ("Jijel", "Bejaia", 30, None, 6297, "de  Djidjil  à Bougie  30  milles"),
    ("Algiers", "Tamenfoust", 18, None, 5859, "D’Alger  à Tàmadfous  (Matifou),  en  se  dirigeant  vers  l’est,  18  milles"),
    ("Bizerte", "Tabarka", 70, None, 7275, "De  Bizerte  à Tabarca  , on  compte  70  milles"),
    ("Monastir", "Mahdia", 30, None, 8024, "D'al-Monastir  à al-Mahdiya  , on  compte  30  milles"),
    ("Tocra", "Ptolemais (Tolmeita)", 50, None, 8513, "De  là  à Tolmaitsa,  50  milles"),
    ("Barca (al-Marj)", "Ajdabiya", 152, 6, 8392, "De  liarca  à Âdjdàfaia , 6 journées  ou  152  milles"),
    ("Barca (al-Marj)", "Alexandria", 550, 21, 8394, "De  Barca  à Alexandrie,  21  journées  ou  550  milles"),
    ("Rosetta (Rashid)", "Alexandria", 60, None, 10097, "De  Rosette  à Alexandrie,  on  compte  60  milles"),
    # Iberia, miles
    ("Cadiz", "Tarifa", 63, None, 11186, "De  Cadix  à Tarifa  , 63  milles"),
    ("Faro (Santa Maria)", "Silves", 28, None, 11223, "De  la  ville  de  Santa-Maria  à celle  de  Silves  , 28  milles"),
    ("Guadalajara", "Medinaceli", 50, None, 11809, "De  Guadalaxara,  en  se  dirigeant  vers  l’orient,  à Medinaceli,  50  milles"),
    ("Daroca", "Zaragoza", 60, None, 11850, "De  Daroca  à Saragosse,  60  milles"),
    ("Calatayud", "Zaragoza", 50, None, 11852, "De  Calatayud  à Saragosse,  également  50  milles"),
    ("Zaragoza", "Huesca", 40, None, 11881, "De  Saragosse  à Uuesca , 40  milles"),
    ("Huesca", "Lleida", 70, None, 11883, "De  Hnesca  à Lérida , 70  milles"),
    ("Mequinenza", "Tortosa", 50, 2, 11890, "De  Mequinenza  à Tortose  on  compte  2 journées  ou  SO  milles"),
    ("Tarragona", "Barcelona", 60, None, 11913, "De  Tarrsgone  à Barcelone,  en  se  dirigeant  vers  l'orient,  60  milles"),
    ("Alzira", "Xativa", 12, None, 11982, "D'Alcira  à Xativa , 12  milles"),
    ("Valencia", "Denia", 65, None, 11992, "De  Valence  à Dénia,  en  suivant  le  golfe'),  65  milles"),
    ("Valencia", "Cullera", 25, None, 11994, "De  Valence  à la  forteresse  de  Cullera,  25  milles"),
    ("Xativa", "Bocairent", 40, None, 12026, "De  Xativa  à Bocayrente,  vers  l'occident'),  40  milles"),
    ("Bocairent", "Denia", 40, None, 12035, "De  Bocayrente  à Dénia,  40  milles"),
    ("Orihuela", "Murcia", 12, None, 12074, "D'Orihuela  à Murcie,  12  milles"),
    ("Cartagena", "Murcia", 40, None, 12153, "De  Carthagènc  à Murcie  on  compte . par  terre , 40  milles"),
    ("Lorca", "Murcia", 40, None, 12299, "De  Lorca  à Murcie  on  compte  40  milles"),
    ("Almunecar", "Granada", 40, None, 12487, "D'Almoftecar  à Grenade,  par  terre,  40  milles"),
    ("Granada", "Loja", 23, None, 12868, "De  Grenade  à Loja,  en  suivant  le  fleuve,  23  milles"),
    ("Almunecar", "Malaga", 80, None, 12872, "D’Almunecar  à Malaga , 80  milles"),
    ("Malaga", "Granada", 80, None, 12890, "De  Maluga  à Grenade,  80  milles"),
    ("Lucena", "Cordoba", 40, None, 12992, "De  Lucena  à Cordoue,  on  compte  40  milles"),
    ("Ecija", "Cordoba", 35, None, 13012, "D’Ëcija  à Cordoue , 35  milles"),
    ("Ecija", "Carmona", 45, None, 13020, "D'Ecija  à Carmona,  45  milles"),
    ("Jerez de la Frontera", "Isla de Leon (San Fernando)", 12, None, 13049, "De  Xérès  à l’ile  de  Cadix  (l’ile  de  Léon),  12  milles"),
    ("Cordoba", "Madinat al-Zahra", 5, None, 13475, "De  Cordoue  à az-Zahrà  on  compte  5 milles"),
    ("Cordoba", "Granada", 100, 4, 13655, "De  Cordoue  à Grenade  on  compte  4 journées  ou  100  milles"),
    # Day stages only
    ("Sale", "Fez", None, 4, 4995, "De  Salà  à Fèz  (Fâs)  , 4 journées"),
    ("Fez", "Sijilmasa", None, 13, 5042, "De  Fèz  à Sidjilmàsa , 13  journées"),
    ("Tlemcen", "Tahert (Tiaret)", None, 4, 5683, "De  Tlemcen  à Tàhart , 4 journées"),
    ("Tenes", "Miliana", None, 2, 5798, "De  Tenès  à Milyâna  , par  terre  , 2 journées"),
    ("M'Sila", "Tobna", None, 2, 6116, "D’al-Masila  on  se  rènd  à Tobna  en  2 journées"),
    ("Tobna", "Bejaia", None, 6, 6130, "De  Tobna  à Bougie,  on  compte  6 journées"),
    ("Constantine", "Bejaia", None, 6, 6295, "De  Constantine  à Bougie,  6 journées"),
    ("Collo", "Constantine", None, 2, 6406, "D’al-Coll  à Constantine,  on  compte  2 journées"),
    ("Setif", "Constantine", None, 4, 6418, "De  Satif  à Constantine , on  compte  4 journées"),
    ("Sfax", "Gafsa", None, 3, 6911, "De  Sfai  à Cafça  , en  se  dirigeant  vers  le  sud-ouest , 3 journées"),
    ("Sfax", "Mahdia", None, 2, 6934, "De  Sfai  à al-Mahdiya  , on  compte  2 journées"),
    ("Kairouan", "Tunis", None, 2, 7097, "D'aUCairawân  à Tunis,  on  compte  un  peu  plus  de  2 journées"),
    ("Barca (al-Marj)", "Awjila", None, 10, 8390, "De  Barca  à Audjala  on  compte,  par  le  désert,  10  journées"),
    ("Fustat (Old Cairo)", "Oxyrhynchus (al-Bahnasa)", None, 7, 10130, "De  Miçr  à al-Bahna$â,  on  compte  7 journées"),
    ("Fustat (Old Cairo)", "Aswan", None, 26, 3886, "De  Miçr  à Syène , on  compte  26  journées"),
    ("Algeciras", "Seville", None, 5, 11025, "D’ Algëziras  à Séville  on  compte  5 journées"),
    ("Silves", "Badajoz", None, 3, 11252, "De  SiWes  à Badajoi  , 3 journées"),
    ("Evora", "Badajoz", None, 2, 11332, "D’Evora  à Badajox,  vers  l’orient,  2 journées"),
    ("Badajoz", "Seville", None, 6, 11356, "De  Badajoz  à Séville  on  compte  6 journées"),
    ("Badajoz", "Cordoba", None, 6, 11359, "De  Badajoz  à Cordoue  par  la  grande  route , 6 journées"),
    ("Merida", "Alcantara", None, 2, 11451, "De  Mérida  à Cantara  as-saif  (Alcantara) , 2 journées"),
    ("Santarem", "Badajoz", None, 4, 11631, "De  Santarcm  à Badajoz  on  compte  4 journées"),
    ("Valencia", "Zaragoza", None, 9, 11969, "De  Valence  à Saragosse,  en  passant  par  Cutanda,  9 journées"),
    ("Murcia", "Valencia", None, 5, 12180, "De  Murcie  à Valence  on  compte  5 journées"),
    ("Murcia", "Almeria", None, 5, 12182, "De  Murcie  à Almérie,  en  suivant  la  côte,  5 journées"),
    ("Cordoba", "Almeria", None, 8, 13489, "De  Cordoue  à Almérie  on  compte  8 journées"),
]

EXTRA = {  # places named in ROUTES that I did not locate on the map
    "Jijel": (36.821, 5.766), "Tamenfoust": (36.806, 3.226), "Bizerte": (37.274, 9.874), "Monastir": (35.777, 10.826),
    "Cadiz": (36.527, -6.288), "Faro (Santa Maria)": (37.019, -7.930), "Daroca": (41.114, -1.414), "Mequinenza": (41.372, 0.301),
    "Tarragona": (41.119, 1.245), "Barcelona": (41.385, 2.173), "Alzira": (39.151, -0.435), "Cullera": (39.164, -0.254),
    "Bocairent": (38.767, -0.612), "Orihuela": (38.085, -0.944), "Loja": (37.169, -4.151), "Lucena": (37.409, -4.485),
    "Carmona": (37.471, -5.646), "Isla de Leon (San Fernando)": (36.463, -6.198), "Madinat al-Zahra": (37.888, -4.867),
    "Tenes": (36.511, 1.306),
}

# Names in the gazetteers under which I looked each identification up (where the name differs from my label)
GAZ_ALIASES = {
    "Fustat (Old Cairo)": ["Fustat", "Misr", "Cairo"], "Constantinople (Istanbul)": ["Istanbul", "Constantinopolis", "Byzantium"],
    "Diyarbakir (Amid)": ["Diyarbakir", "Amida", "Amid"], "Erzurum (Qaliqala)": ["Erzurum", "Qaliqala", "Theodosiopolis"],
    "Kahramanmaras": ["Kahramanmaras", "Germanicia", "Marash"], "Tahert (Tiaret)": ["Tiaret", "Tahart", "Tahert"],
    "Daybul (Banbhore)": ["Daybul", "Dabil"], "Bost (Lashkar Gah)": ["Bust", "Lashkar Gah"], "Kyiv": ["Kiev", "Kyiv"],
}
