from bs4 import BeautifulSoup
import requests
import stripe
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler
import os
import urllib.parse

stripe.api_key = os.environ['STRIPE_SECRET_KEY']
 
class handler(BaseHTTPRequestHandler):
  def do_GET(self):
    query = urllib.parse.urlparse(self.path).query
    params = urllib.parse.parse_qs(query)
    checkout = stripe.checkout.Session.retrieve(params["session"][0])
    if checkout.payment_status != "paid" or datetime.fromtimestamp(checkout.created) < datetime.now() - timedelta(minutes=15):
      self.send_response(200)
      self.send_header('Content-type','text/html')
      self.end_headers()
      self.wfile.write(f"""<html>
  <head>
    <title>Stash - Failed</title>
  </head>
  <body>
    <p>Payment failed.</p>
  </body>
</html>
""".encode('utf-8'))
      return

    session = requests.Session() 

    response = session.get("https://enterprise.masterlockvault.com/startupshell/Account/Login/")
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    token_input = soup.find('input', attrs={'name': '__RequestVerificationToken'})
    response = session.post("https://enterprise.masterlockvault.com/startupshell/Account/Login/", data={
      "__RequestVerificationToken":token_input['value'],
      "Email":"robertgeorge@startupshell.org",
      "Password":"##dknRk%9@SG9rcL"
    })
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    token_input = soup.find('input', attrs={'name': '__RequestVerificationToken'})

    now = datetime.now(timezone.utc)
    next_time = (now - timedelta(hours=now.hour % 4)).replace(minute=0, second=0, microsecond=0)

    response = session.post("https://enterprise.masterlockvault.com/api/deviceTac", json={
      "deviceIdentifier":"A30QYZ",
      "lockId":120159,
      "requestedAccessTime":next_time.isoformat(),
      "localOffset":-240,
      "slot":1
    }, headers={
      "X-XSRF-TOKEN": token_input['value']
    })

    self.send_response(200)
    self.send_header('Content-type','text/html')
    self.end_headers()
    self.wfile.write(f"""<html>
  <head>
    <title>Stash - Success</title>
  </head>
  <body>
    <p>Payment successful. Use this code to unlock Locker 36: {response.json()["passcode"]}</p>
  </body>
</html>
""".encode('utf-8'))
