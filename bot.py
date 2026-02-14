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
                # Récupération du titre et du lien dans le H3
                h3 = block.find('h3')
                if not h3: continue
                titre = h3.get_text(strip=True)
                
                # On cherche le lien soit dans le h3, soit dans le bloc
                link_tag = h3.find('a', href=True) or block.find('a', href=True)
                raw_url = link_tag['href'] if link_tag else "#"
                url = raw_url if raw_url.startswith('http') else "https://www.bdphile.fr" + raw_url
                
                # Editeur
                editeur = "Inconnu"
                pub_link = block.find('a', href=lambda x: x and '/publisher/' in x)
                if pub_link:
                    editeur = pub_link.get_text(strip=True)

                # Lien Amazon automatique
                search_amazon = f"https://www.amazon.fr/s?k={titre.replace(' ', '+')}+bd"

                item = f'''
                <li style="margin-bottom: 10px; list-style: none; border-bottom: 1px solid #eee; padding-bottom: 5px;">
                    <a href="{url}" style="text-decoration:none; color:#2980b9; font-weight:bold; font-size:15px;">{titre}</a> 
                    <br><span style="color:#666; font-size:13px;">Editeur : {editeur}</span>
                    <a href="{search_amazon}" style="margin-left:10px; font-size:11px; color:#e67e22; border:1px solid #e67e22; border-radius:3px; padding:2px 6px; text-decoration:none; font-weight:bold;">🛒 AMAZON</a>
                </li>'''
                
                if item not in planning[current_date]:
                    planning[current_date].append(item)

    total = sum(len(v) for v in planning.values())
    if total > 0:
        html = '<div style="font-family: Helvetica, Arial, sans-serif; max-width: 600px; margin: auto; border: 1px solid #ddd; padding: 20px; border-radius: 10px;">'
        html += '<h1 style="color: #2c3e50; text-align: center; border-bottom: 3px solid #3498db; padding-bottom: 10px;">📚 Tes Sorties BD</h1>'
        html += f'<p style="text-align:center; color:#7f8c8d;">{total} nouveautés détectées pour la semaine prochaine</p>'

        for date, bds in planning.items():
            if bds:
                html += f'<h3 style="background: #3498db; padding: 10px; color: white; border-radius: 5px; margin-top: 25px;">📅 {date}</h3>'
                html += '<ul style="padding: 0;">' + "".join(bds) + '</ul>'
        html += '</div>'

        resend.Emails.send({
            "from": "AksoumBot 📚 <bot@gangdessine.com>",
            "to": ["sacha.okonowski@gmail.com"],
            "subject": f"📚 Planning : {total} BD cette semaine",
            "html": html
        })
        print(f"📧 Mail envoyé avec succès !")
    else:
        print("❌ Aucune BD trouvée.")

if __name__ == '__main__':
    run()
