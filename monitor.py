import os
import smtplib
from email.message import EmailMessage
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops

# Seznam služeb k monitorování
SERVICES = {
    "TVCOM": "https://www.tvcom.cz/",
    "Disney+": "https://www.disneyplus.com/eu/cs-cz/home",
    "Netflix": "https://www.netflix.com/cz/",
    "Prime Video": "https://www.primevideo.com/",
    "Oneplay": "https://www.oneplay.cz/",
    "iVysílání": "https://www.ceskatelevize.cz/ivysilani/",
    "HBO Max (Max)": "https://www.hbomax.com/cz/cs",
    "SkyShowtime": "https://www.skyshowtime.com/watch/home",
    "Apple TV": "https://tv.apple.com/cz?l=cs",
    "Starmax": "https://starmax.tv/screens/home",
    "Canal+": "https://www.canalplus.cz/",
    "KVIFF.TV": "https://kviff.tv/",
    "DaFilms": "https://dafilms.cz/",
    "Dramox": "https://www.dramox.cz/",
    "Spotify": "https://open.spotify.com/",
    "Apple Music": "https://music.apple.com/us/new",
    "Tidal": "https://tidal.com/",
    "Deezer": "https://www.deezer.com/cs/",
    "Stargaze": "https://stargaze.com/screens/home",
    "DVTV": "https://dvtv.cz/",
    "YouTube": "https://www.youtube.com/",
    "Skylink": "https://livetv.skylink.cz/"
}

SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

changes_detected = []

def send_email(subject, body):
    sender = os.environ.get("MAIL_USER")
    password = os.environ.get("MAIL_PASS")
    receiver = os.environ.get("MAIL_TO")
    
    if not sender or not password or not receiver:
        print("E-mailové údaje nejsou nastaveny v proměnných prostředí.")
        return

    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver

    try:
        # Příklad pro Gmail (lze upravit dle poskytovatele)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        print("E-mail byl úspěšně odeslán.")
    except Exception as e:
        print(f"Chyba při odesílání e-mailu: {e}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    
    for name, url in SERVICES.items():
        print(f"Kontroluji: {name}...")
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        try:
            # Otevře stránku a počká na síťový klid (aby se načetly bannery/menu)
            page.goto(url, timeout=60000, wait_until="networkidle")
            
            new_path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
            page.screenshot(path=new_path, full_page=False)
            
            old_path = os.path.join(SCREENSHOT_DIR, f"{name}_old.png")
            
            # Pokud existuje starý screenshot, porovnáme je
            if os.path.exists(old_path):
                img1 = Image.open(old_path)
                img2 = Image.open(new_path)
                
                # Porovnání obrázků
                diff = ImageChops.difference(img1, img2)
                if diff.getbbox():
                    changes_detected.append(name)
                    print(f"-> Zjištěna změna u: {name}")
                else:
                    print(f"-> Bez změn: {name}")
            else:
                print(f"-> První spuštění pro: {name}")
            
            # Aktualizujeme starý screenshot na nový pro příští porovnání
            if os.path.exists(new_path):
                img_new = Image.open(new_path)
                img_new.save(old_path)
                
        except Exception as e:
            print(f"Chyba při načítání {name}: {e}")
            
    browser.close()

# Pokud byly detekovány změny, odešleme e-mail
if changes_detected:
    subject = f"Monitor služeb: Změny u {len(changes_detected)} služeb"
    body = "Následující služby zaznamenaly změnu vzhledu nebo obsahu na hlavní stránce:\n\n"
    for s in changes_detected:
        body += f"- {s} ({SERVICES[s]})\n"
    send_email(subject, body)
else:
    print("Žádné vizuální změny nebyly detekovány.")
