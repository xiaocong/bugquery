BugReporterServer

Structure Map:
bugquery/   The front-end of the server, for user querying bug report.
brstore/    Application mainly for storing report data, based on MongoDB.
brquery/    Application mainly for querying report data, based on Redis.
brauth/     Application for authentication and authorization.
doc/        Project related documents.
lib/        Some necessary library


Prerequisite:
1.Install pyexcelerator(in lib/)
2.Install suds(easy_install suds)


Release notes:



How to config a server?
Install Ubuntu 10.04 LTS.(32-bit vs 64-bit/ server vs destop)



Install easy_install
sudo apt-get install python-setuptools

Install suds(lib for accessing web service)
sudo easy_install suds

Install pyexcelerator(/lib/pyexcelerator/)
sudo python ./setup.py install

Install bottle
sudo easy_install bottle

2.Install Apache2
sudo apt-get install apache2
sudo apt-get install libapache2-mod-wsgi
sudo a2enmod proxy
sudo vi /etc/apache2/mods-enabled/wsgi.conf   :#WSGIRestrictStdout On  --> WSGIRestrictStdout Off


Install MongoDB(32-bit vs 64-bit)
32-bit:
wget http://fastdl.mongodb.org/linux/mongodb-linux-i686-2.0.6.tgz
64-bit:
wget http://fastdl.mongodb.org/linux/mongodb-linux-x86_64-2.0.6.tgz
Install pymongo:
sudo easy_install pymongo


Install Redis
$ wget http://redis.googlecode.com/files/redis-2.4.14.tar.gz
$ tar xzf redis-2.4.14.tar.gz
$ cd redis-2.4.14
$ make
In order to install Redis binaries into /usr/local/bin just use:
make install
Install redis-py:
sudo easy_install redis




