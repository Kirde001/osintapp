apt update && apt upgrade -y
apt install python3-venv python3-pip nginx -y

mkdir -p /root/osint/templates
cd /root/osint/
python3 -m venv venv
source venv/bin/activate

nano requirements.txt
pip install -r requirements.txt

nano /etc/systemd/system/osintapp.service
systemctl daemon-reload
systemctl start osintapp
systemctl enable osintapp

nano /etc/nginx/sites-available/osintapp
ln -s /etc/nginx/sites-available/osintapp /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

systemctl restart osintapp
systemctl status osintapp
systemctl status nginx

автоматизация
python3 fetch_key.py (один раз самостоятельно - потом в cron)
crontab -e (0 0 * * * /root/osint/venv/bin/python /root/osint/fetch_key.py >> /root/osint/cron_log.log 2>&1)
