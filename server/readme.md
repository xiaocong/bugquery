# Directories Layout

  bugquery/    The front-end of the server, for user querying bug report.

  reporter/    Application provides service for bugreporter related business.

  brauth/      Application provides service for authentication and authorization.

  doc/         Project related documents.


# Prerequirement

  1. Ubuntu 10.04 LTS and above

  2. python 2.6 or python 2.7 (preferred)


# Installation

- Python Packages.

  $ sudo pip install suds

  $ sudo pip install pyexcelerator`

  $ sudo pip install bottle

  $ sudo pip install redis

  $ sudo pip install pymongo

- Install Apache2 server and modules for deployment

  $ sudo apt-get install apache2

  $ sudo apt-get install libapache2-mod-wsgi

  $ sudo a2enmod proxy

- Install mongodb server for deployment

  Before running the server, you must set up `mongodb`, `redis` on your local PC

  $ sudo apt-get install mongodb memcached redis-server

# Run the server (deployment)

- Running the app with gevent server

  $ python app.py

- Running the app with apache server

  $ sudo vi /etc/apache2/mods-enabled/wsgi.conf
     
    modify line

         "WSGIRestrictStdout On"  -> "WSGIRestrictStdout Off"
        
  $ sudo vi /etc/apache2/ports.conf
     
    add lines

         NameVirtualHost *:8010
         Listen 8010


  $ sudo vi /etc/apache2/sites-enabled/000-default 
     
    add lines

        <VirtualHost *:8010>
        ServerAdmin webmaster@localhost
        DocumentRoot /var/www/
        WSGIDaemonProcess reporter user=www-data group=www-data processes=1 threads=30
        WSGIScriptAlias /api/brquery /path/to/bugquery/server/reporter/reporter.wsgi
        <Directory /path/to/bugquery/server/reporter/>
            WSGIProcessGroup reporter
            WSGIApplicationGroup %{GLOBAL}
            Order deny,allow
            Allow from all
        </Directory>
        WSGIDaemonProcess brauth user=www-data group=www-data processes=1 threads=10
        WSGIScriptAlias /api/brauth /path/to/bugquery/server/brauth/brauth.wsgi
        <Directory /path/to/bugquery/server/brauth/>
            WSGIProcessGroup brauth
            WSGIApplicationGroup %{GLOBAL}
            Order deny,allow
            Allow from all 
        </Directory>
        ErrorLog /var/log/apache2/bugquery.error.log
        # Possible values include: debug, info, notice, warn, error, crit,
        # alert, emerg.
        LogLevel info
        CustomLog /var/log/apache2/bugquery.access.log combined
        </VirtualHost>

  $ sudo /etc/init.d/apache2 reload