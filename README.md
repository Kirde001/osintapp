# В коде используются публичные API-токены, которые обновляются каждый час (так что ценности для парсеров они не имеют)

# Основная установка
```bash
apt update && apt upgrade -y
apt install python3-venv python3-pip nginx -y
```
# Основа проекта + изолированное окружение
```bash
mkdir -p /root/osint/templates
cd /root/osint/
python3 -m venv venv
source venv/bin/activate
```
# Зависимости
```bash
nano requirements.txt
pip install -r requirements.txt
```
# Сервис
```bash
nano /etc/systemd/system/osintapp.service
systemctl daemon-reload
systemctl start osintapp
systemctl enable osintapp
```
# Прокся в nginx 
```bash
nano /etc/nginx/sites-available/osintapp
ln -s /etc/nginx/sites-available/osintapp /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx
```
# Запуск 
```bash
systemctl restart osintapp
systemctl status osintapp
systemctl status nginx
```
# Автоматизация
```bash
python3 fetch_key.py 
```
# Достаточно один раз запустить самостоятельно - потом в cron
```bash
crontab -e 
0 0 * * * /root/osint/venv/bin/python /root/osint/fetch_key.py >> /root/osint/cron_log.log 2>&1
```