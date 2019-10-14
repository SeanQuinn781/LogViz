Deploying using Nginx/Gunicorn/systemd:

1. Move LogViz into /var/www/html/LogViz
2.
```
cd /var/www/html/LogViz && source LogViz/bin/activate
```
3. add gunicorn to requirements.txt and:
```
sudo pip install --user -r requirements.txt
```
4. test the app on port 5000 by running with only gunicorn
5. Add the systemctl service LogViz LogViz.service to /etc/systemd/system, start it and make sure it works:
```
sudo systemctl start LogViz && sudo systemctl status LogViz
```

enable on startup:

```
sudo systemctl enable LogViz
```

6. Install Nginx and use the website conf provided in this folder by moving it into /etc/nginx/sites-enabled/

sudo nginx -t
sudo service nginx restart

For more details use the instructions from Digital ocean in this folder


