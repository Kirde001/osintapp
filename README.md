# основная установка
```bash
apt update && apt upgrade -y
apt install python3-venv python3-pip nginx -y
```
# основа проекта + изолированное окружение
```bash
mkdir -p /root/osint/templates
cd /root/osint/
python3 -m venv venv
source venv/bin/activate
```
# зависимости
```bash
nano requirements.txt
pip install -r requirements.txt
```
# сервис
```bash
nano /etc/systemd/system/osintapp.service
systemctl daemon-reload
systemctl start osintapp
systemctl enable osintapp
```
# прокся в nginx 
```bash
nano /etc/nginx/sites-available/osintapp
ln -s /etc/nginx/sites-available/osintapp /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx
```
# запуск 
```bash
systemctl restart osintapp
systemctl status osintapp
systemctl status nginx
```
# автоматизация
```bash
python3 fetch_key.py (один раз самостоятельно - потом в cron)
crontab -e (0 0 * * * /root/osint/venv/bin/python /root/osint/fetch_key.py >> /root/osint/cron_log.log 2>&1)
```