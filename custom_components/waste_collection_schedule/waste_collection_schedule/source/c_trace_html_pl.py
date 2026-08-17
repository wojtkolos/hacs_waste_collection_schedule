import datetime
import logging
import requests
import re
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

_LOGGER = logging.getLogger(__name__)

DESCRIPTION = "Skrypt HTML dla dawnego systemu ZM GOAP (c-trace)."
URL = "https://web.c-trace.de"
TITLE = "C-Trace (HTML) PL"

class Source:
    def __init__(self, service, ort, strasse, hausnummer):
        self._service = service
        self._ort = ort
        self._strasse = strasse
        self._hausnummer = str(hausnummer)

    def fetch(self):
        session = requests.Session()
        
        # 1. Wejście na stronę główną, aby serwer wygenerował w URL token sesji (np. /(S(...))/)
        base_url = f"https://web.c-trace.de/{self._service}-abfallkalender/kalendarzodpadow"
        
        # allow_redirects=True sprawia, że requests podąży za przekierowaniem 302 do tokenizowanego URL
        response_get = session.get(base_url, allow_redirects=True)
        response_get.encoding = 'utf-8'
        
        # Łapiemy nowy URL (z tokenem), na który będziemy wysyłać formularz
        current_url = response_get.url
        
        # 2. Wysłanie żądania POST z parametrami (dokładnie takimi, jak w HTML)
        payload = {
            "ort": self._ort,
            "strasse": self._strasse,
            "hausnr": self._hausnummer,
            "objekttyp": "",
            "objekttyp2": "",
            "posted": "yes",
            "Odczyt": "Odczyt"
        }
        
        response_post = session.post(current_url, data=payload)
        response_post.encoding = 'utf-8'
        
        # 3. Parsowanie zwróconego HTML
        soup = BeautifulSoup(response_post.text, "html.parser")
        entries = []
        
        # Wyszukujemy wszystkie kafelki z kalendarzem
        plans = soup.find_all("div", class_="plan")
        
        for plan in plans:
            tour_div = plan.find("div", class_="tour")
            if not tour_div:
                continue
            
            waste_type = tour_div.text.strip()
            
            # Mapowanie skrótów na pełne nazwy i ikony
            icon = "mdi:trash-can"
            if waste_type == "ZM":
                waste_name = "Zmieszane"
                icon = "mdi:delete-empty"
            elif waste_type == "SZK":
                waste_name = "Szkło"
                icon = "mdi:bottle-wine"
            elif waste_type == "PAP":
                waste_name = "Papier"
                icon = "mdi:newspaper"
            elif waste_type == "TWS":
                waste_name = "Tworzywa Sztuczne"
                icon = "mdi:recycle"
            elif waste_type == "BIO":
                waste_name = "Bio"
                icon = "mdi:leaf"
            elif waste_type == "GAB":
                waste_name = "Gabaryty"
                icon = "mdi:sofa"
            else:
                waste_name = waste_type
                
            termine_ul = plan.find("ul", class_="termine")
            if not termine_ul:
                continue
                
            for li in termine_ul.find_all("li"):
                date_str = li.text.strip()
                # Używamy wyrażenia regularnego, żeby wyciągnąć samą datę z formatu "pt., 28.08.2026"
                match = re.search(r'\d{2}\.\d{2}\.\d{4}', date_str)
                if match:
                    parsed_date = datetime.datetime.strptime(match.group(), "%d.%m.%Y").date()
                    entries.append(Collection(
                        date=parsed_date,
                        t=waste_name,
                        icon=icon
                    ))
                    
        if not entries:
            _LOGGER.warning("Skrypt zadziałał, ale nie znalazł dat. Sprawdź, czy adres jest poprawny.")
            
        return entries