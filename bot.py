import requests
from bs4 import BeautifulSoup
import os
import resend
from datetime import datetime, timedelta

resend.api_key = os.environ.get("RESEND_API_KEY")

def run():
    today = datetime.now()
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0: days_until_monday = 7
    start_mon = today + timedelta(days=days_until_monday)
    
    mois_fr = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
    dates_semaine = [f"{(start_mon + timedelta(days=i)).day} {mois_fr[(start_mon + timedelta(days=i)).month-1]} {(start_mon + timedelta(days=i)).year}" for i in range(7)]
    
    # On prépare un dictionnaire pour ranger par jour
    planning = {d: [] for d in dates_semaine}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    print(f"🔎 Scan des pages pour la semaine...")

    for page in range(10):
        r = requests.get(f"https://www.bdphile.fr/sortie-bd/?start={page*25}", headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        for block in soup.find_all('div', style=lambda x: x and 'min-height' in x):
            txt = block.get_text()
            
            # 1. Identification du jour
            current_date = None
            for d in dates_semaine:
                if d in txt:
                    current_date = d
                    break
            
            if current_date:
                # 2. Titre (h3)
                h3 = block.find('h3')
                if not h3: continue
                titre = h3.get_text(strip=True)
                
                # 3. URL
                link = block.find('a', href=True)
                url = "https://www.bdphile.fr" + link['href'] if link else "#"
                
                # 4. Editeur
                editeur = "Inconnu"
                pub_link = block.find('a', href=lambda x: x and '/publisher/' in x)
                if pub_link:
                    editeur = pub_link.get_text(strip=True)
                
                item = f'<li><a href="{url}">{titre}</a> <span style="color:#666;">({editeur})</span></li>'
                if item not in planning[current_date]:
                    planning[current_date].append(item)
                    print(f"✅ [{current_date}] : {titre}")

    # Construction du mail avec séparation
    total = sum(len(v) for v in planning.values())
    if total > 0:
        html = '<div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">'
        html += '<h1 style="color: #2c3e50; text-align: center; border-bottom: 2px solid #3498db; padding-bottom: 10px;">📚 Tes Sorties BD</h1>'
        
        for date, bds in planning.items():
            if bds:
                html += f'<h3 style="background: #ecf0f1; padding: 10px; border-left: 5px solid #3498db; color: #2980b9;">📅 {date}</h3>'
                html += '<ul style="list-style-type: none; padding-left: 10px;">' + "".join(bds) + '</ul>'
        
        html += '</div>'

        resend.Emails.send({
            "from": "AksoumBot <onboarding@resend.dev>",
            "to": ["sacha.okonowski@gmail.com"],
            "subject": f"📚 Planning : {total} BD cette semaine",
            "html": html
        })
        print(f"📧 Mail envoyé avec {total} BD triées par jour.")
    else:
        print("❌ Aucune BD trouvée pour cette période.")

if __name__ == '__main__':
    run()
