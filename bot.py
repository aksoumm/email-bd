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
    
    planning = {d: [] for d in dates_semaine}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    for page in range(10):
        r = requests.get(f"https://www.bdphile.fr/sortie-bd/?start={page*25}", headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        for block in soup.find_all('div', style=lambda x: x and 'min-height' in x):
            txt = block.get_text()
            current_date = next((d for d in dates_semaine if d in txt), None)
            
            if current_date:
                h3 = block.find('h3')
                if not h3: continue
                titre = h3.get_text(strip=True)
                link = block.find('a', href=True)
                url = link['href'] if link else "#"
                
                editeur = "Inconnu"
                pub_link = block.find('a', href=lambda x: x and '/publisher/' in x)
                if pub_link:
                    editeur = pub_link.get_text(strip=True)
                
                item = f'<li><a href="{url}">{titre}</a> <span style="color:#666;">({editeur})</span></li>'
                if item not in planning[current_date]:
                    planning[current_date].append(item)

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
        print(f"✅ Mail envoyé avec {total} BD.")
