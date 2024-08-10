# SS2DTournamentRunner

**Django4** based application for managing Soccer Simulation 2D Tournament. With using this tool participant in can upload team binary and select binary for match and test their codes.

## Requirements

* Python3
* Docker
    <https://docs.docker.com/engine/install/ubuntu/>
* Redis

    ```bash
    docker pull redis
    ```

production:

* Apache2
* OpenSSL

    ```bash
    sudo apt-get install libssl-dev
    ```

## First time setup

1. Run Redis
    Redis is required for django queue.

    ```bash
    docker run --name test-redis -p 127.0.0.1:6379:6379 -d redis redis-server --save 60 1 --loglevel warning
    ```

2. Create virtualenv
    The next step is to create a Python virtual environment so that our Django will be separate from the system’s tools and any other Python projects we may be working on.

    ```bash
    sudo apt-get update
    sudo apt-get install python3-pip
    sudo pip install virtualenv

    python3 -m virtualenv venv
   
    source venv/bin/activate
    ```

3. Install requirements

    ```bash
    pip install -r requirements.txt
    ```

4. Apply first schema to DB

    ```bash
    python manage.py migrate
    ```

5. Create superuser
    Create an administrative user for the project by typing:

    ```bash
    python manage.py createsuperuser
    ```

6. First setup complete do Run Development next.

### Run Development

1. Source virtualenv

    ```bash
    source venv/bin/activate
    ```

2. Start redis

    ```bash
    docker start test-redis
    ```

3. Run Django Server
    you can test your project by starting up the Django development server with this command:

    ```bash
    python manage.py runserver
    # OR
    ./manage.py runserver 0.0.0.0:8000
    ```

    In your web browser, visit your server’s domain name or IP address followed by `:8000` or simply your `localhost:8000` :

    ```url
    http://server_domain_or_IP:8000
    ```

    If you append /admin to the end of the URL in the address bar, you will be prompted for the administrative username and password you created with the createsuperuser command and After authenticating, you can access the default Django admin interface.

4. Run Django Queue

    ```bash
    python manage.py rqworker default
    ```

## Production setup

### Deploying Apache Web Server

We need to collect all of the static content into the directory location we configured in setting.py by typing this command in your project directory.

```bash
./manage.py collectstatic
```

You will have to confirm the operation. The static files will be placed in a directory called `assets` within your project directory.

To get everything we need, update your server’s local package index and then install the appropriate packages.

```bash
sudo apt-get update
sudo apt-get install apache2 libapache2-mod-wsgi-py3
sudo apt-get install apache2-dev python3-dev # if somthing is wrong with libapache2-mod-wsgi-py3
```

Client connections that Apache receives will be translated into the `WSGI` format that the Django application expects using the `mod_wsgi` module. This should have been automatically enabled upon installation if there is a problem with `mod_wsgi` follow this follow these instructions.

#### mod_wsi alternative way

Source code tar balls can be obtained from:
    <https://github.com/GrahamDumpleton/mod_wsgi/releases>

After having downloaded the tar ball for the version you want to use, unpack it with the command:

```bash
tar xvfz mod_wsgi-X.Y.tar.gz
```

Replace ‘X.Y’ with the actual version number for that being used.

To setup the package ready for building run the `configure` script from within the source code directory and Once the package has been configured, it can be built by running `make` and then install the Apache module into the standard location for Apache modules as dictated by Apache for your installation by running `sudo make install`:

```bash
./configure --with-python=<<path_to_your_project_venv_folder>>/bin/python
make
sudo make install
```

Installation should be done as the ‘root’ user or ‘sudo’ command if appropriate.

Once the Apache module has been installed into your Apache installation’s module directory, it is still necessary to configure Apache to actually load the module.

In the simplest case, all that is required is to add a line of the form:

```apacheconf
LoadModule wsgi_module modules/mod_wsgi.so
```

into the main Apache (`httpd.conf` or `apache.conf`) configuration file at the same point that other Apache modules are being loaded. the last option to the directive should either be an absolute path to where the mod_wsgi module file is located, or a path expressed relative to the root of your Apache installation. If you used “make” to install the package, see where it copied the file to work out what to set this value to.

Having adding the required directives you should perform a restart of Apache to check everything is okay. If you are using an unmodified Apache distribution from the Apache Software Foundation, a restart is performed using the ‘apachectl’ command:

```bash
apachectl restart # add sudo if necessary
```

If you see any sort of problem, or if you are upgrading from an older version of mod_wsgi, it is recommended you actually stop and the start Apache instead:

```bash
apachectl stop # add sudo if necessary
apachectl start # add sudo if necessary
```

#### Configure the Apache server

Now we can configure Apache as a server end.

To configure the WSGI pass, we’ll need to edit the default virtual host file:

```bash
sudo nano /etc/apache2/sites-available/000-default.conf
```

We can keep the directives that are already present in the file. We just need to add some additional items. There is an example .conf file in doc folder. remove doc folder in production for more safety.

```apacheconf
<VirtualHost *:80>
    . . .


    Alias /static <<path_to_your_project_folder>>/assets
    <Directory <<path_to_your_project_folder>>/assets>
        Require all granted
    </Directory>

    Alias /robots.txt <<path_to_your_project_folder>>/robots.txt
    Alias /favicon.ico <<path_to_your_project_folder>>/static/favicon.ico

    Alias /media/ <<path_to_your_project_folder>>/upload/
    Alias /upload/ <<path_to_your_project_folder>>/upload/

    <Directory <<path_to_your_project_folder>>/upload/>
      Require all granted
    </Directory>

    <Directory <<path_to_your_project_folder>>/<<project_name>>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>

    WSGIDaemonProcess <<project_name>> python-path=<<path_to_your_project_folder>> python-home=<<path_to_your_project_venv_folder>>
    WSGIProcessGroup <<project_name>>
    WSGIScriptAlias / <<path_to_your_project_folder>>/<<project_name>>/wsgi.py

</VirtualHost>
```

When you are finished making these changes, save and close the file.

#### Some Apache Permissions Issues

If you are using the SQLite database, which is the default used in this project, you need to allow the Apache process access to this file.

To do so, the first step is to change the permissions so that the group owner of the database can read and write. The database file is called db.sqlite3 by default and it should be located in your base project directory:

```bash
chmod 664 <<path_to_your_project_folder>>/db.sqlite3
```

Afterwards, we need to give the group Apache runs under, the <APACHE_RUN_GROUP> (by-default is www-data group), group ownership of the file:

```bash
sudo chown :<APACHE_RUN_GROUP>  <<path_to_your_project_folder>>/db.sqlite3
```

In order to write to the file, we also need to give the Apache group ownership over the database’s parent directory:

```bash
sudo chown :<APACHE_RUN_GROUP> -R <<path_to_your_project_folder>>
sudo chmod g+w -R <<path_to_your_project_folder>>
```

Once these steps are done, you are ready to restart the Apache service to implement the changes you made. Restart Apache by typing:

```bash
sudo apachectl restart
# OR
sudo service apache2 restart
```

You should now be able to access site by going to your server’s domain name or IP address without specifying a port. The regular site and the admin interface should function as expected.

### Deploying RQWorker Service

Create an rqworker service that runs the high, default, and low queues.

```bash
sudo nano /etc/systemd/system/rqworker.service
```

```bash
[Unit]
Description="Django-RQ Worker"
After=network.target

[Service]
WorkingDirectory=<<path_to_your_project_folder>>
ExecStart=<<path_to_your_project_venv_folder>>/bin/python \
    <<path_to_your_project_folder>>/manage.py \
    rqworker default # you can add high low too 

[Install]
WantedBy=multi-user.target
```

Enable and start the service

```bash
sudo systemctl enable rqworker
sudo systemctl start rqworker
```

You must reload or restart RQWorker or Workers after any change to apply them for your queues. you can do this manualy by restarting the service.

```bash
sudo systemctl restart rqworker
```

You can however let systemd auto-restart it in case it fails or is accidentally killed. To do so, you can add the Restart option to the [Service] stanza.

```bash
# ...
StartLimitIntervalSec=500
StartLimitBurst=5

[Service]
Restart=on-failure
RestartSec=5s
# ...
```

The above will react to anything that stops your worker: a code exception, someone that does `kill -9 pid`, … as soon as your worker stops, systemd will restart it in 5 seconds.

In this example, there are also `StartLimitIntervalSec` and `StartLimitBurst` directives in the [Unit] section.
This prevents a failing service from being restarted every 5 seconds. This will give it 5 attempts, if it still fails, systemd will stop trying to start the service.

Note: if you change your systemd unit file, make sure to run `systemctl daemon-reload` to reload the changes.

If you ask for the status of your worker after it’s been killed, systemd will show `activating (auto-restart)`.

#### Adding a RQWorker Watcher Service to reload-or-restart on file change

You can add a watcher for checking any file change and restart the RQWorker, use this only for development and disable it after your testing.

```bash
sudo nano /etc/systemd/system/rqworker-bigbro.service
```

```bash
[Unit]
Description=Django-RQ Watcher
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/systemctl restart rqworker.service

[Install]
WantedBy=multi-user.target
```

```bash
sudo nano /etc/systemd/system/rqworker-bigbro.path
```

```bash
[Path]
PathModified=<<path_to_your_target_folder>>

[Install]
WantedBy=multi-user.target
```

Enable and start the watcher-service (only for development / Disable in production)

```bash
sudo systemctl enable rqworker-bigbro.path
sudo systemctl start rqworker-bigbro.path
```

#### Run Multiple Instance of the RQWorker Service to Manage More Servers

By appending the `@` symbol to the unit file name, it becomes a template unit file and can be called multiple times.

For example, if we request a service called `rqworker@1.service`, systemd will first look for an exact filename match in its available unit files. If nothing is found, it will look for a file called `rqworker@.service`.

That last file will then be used to instantiate the unit based on the argument it was passed. In our example, the argument is 1, but it can be any string.

You can then access this argument by using the %i identifier in your unit file.

```bash
sudo nano /etc/systemd/system/rqworker@.service
```

```bash
[Unit]
Description="Django-RQ Worker instance #%i"
After=network.target

[Service]
WorkingDirectory=<<path_to_your_project_folder>>
ExecStart=/home/ubuntu/.virtualenv/<<your_virtualenv>>/bin/python \
    <<path_to_your_project_folder>>/manage.py \
    rqworker default # you can add high low too
```

We can test this by reloading the systemd configuration and starting two instances of the service:

```bash
sudo systemctl daemon-reload
sudo systemctl start rqworker@1.service rqworker@2.service
```

You can now manage each service individually with systemd. For example, you can stop one of them and check on the status of the other:

```bash
systemctl stop rqworker@1.service
systemctl status rqworker@2.service
```

#### Use a target file to manage all instances

It would be much easier if we could manage all of them with a single unit, instead of having to repeat every instance argument each time. We can group these units by creating a target unit. Create this unit file by this command:

```bash
sudo nano /etc/systemd/system/rqworkers.target
```

We define all the services we need in the `Wants=` directive. This will make sure the instances we need are started when we invoke this target.

```bash
[Unit]
Description="Django-RQ Workers"
Wants=rqworker@1.service rqworker@2.service rqworker@3.service rqworker@4.service

[Install]
WantedBy=multi-user.target
```

```bash
# start all instances by invoking the new target
sudo systemctl start rqworkers.target
# check the systemd status for each worker indvidually:
sudo systemctl status rqworker@1.service rqworker@2.service rqworker@3.service rqworker@4.service
# stop one worker or any number of them:

sudo systemctl stop rqworker@1.service

sudo systemctl stop rqworker@1.service rqworker@2.service rqworker@3.serv
ice rqworker@4.service
```

If everything is working as expected, enable the unit so it will start on with each boot:

```bash
sudo systemctl enable rqworkers.target
sudo systemctl start rqworkers.target
```

 you can use `Requires=` insted of  `Wants=` and using the `Requires=` directive will restart all workers (including the target service) when one of them is restarted if `Restart=always` is set. WE recommend to use `Wants=`, which is a weaker version of `Requires=`. `Wants=` will only start when the related unit is started, but will not be stopped or restarted along with the related unit.

Stopping the `rqworkers.target` unit will also stop all worker instances only if we use `Requires=` insted of `Wants=`:

```bash
sudo systemctl stop rqworkers.target.
```

### Project Setting and Configs

TODO:

* [ ] dotenv

    ```bash
    docker_script_path='<<SS2D-Docker-Tournament-location>>'
    ```

* [ ] setting.py

  * SECURITY

    ```python
    # SECRET_KEY = os.environ['SECRET_KEY'] # production 
    # SECURITY WARNING: don't run with debug turned on in production!
    DEBUG = False
    # SECURITY WARNING: This is a security measure to prevent HTTP Host header attacks.
    # A list of strings representing the host/domain names that this Django site can serve.
    ALLOWED_HOSTS = ['127.0.0.1']
    # A list of trusted origins for unsafe requests.
    # CSRF_TRUSTED_ORIGINS = ['']

    # SECURITY WARNING: you may want to either set this setting True or configure a load balancer
    # or reverse-proxy server to redirect all connections to HTTPS.
    SECURE_SSL_REDIRECT = True # production with SSL only

    # SECURITY WARNING: Using a secure-only session cookie makes it more difficult for
    # network traffic sniffers to hijack user sessions.
    SESSION_COOKIE_SECURE = True # production with SSL only

    # SECURITY WARNING: Using a secure-only CSRF cookie makes it more difficult for network
    # traffic sniffers to steal the CSRF token.
    CSRF_COOKIE_SECURE = True # production with SSL only

    ## HTTP Strict Transport Security
    # SECURITY WARNING: If your entire site is served only over SSL,
    # you may want to consider setting a value and enabling HTTP Strict Transport Security.
    SECURE_HSTS_SECONDS = 31536000 # production with SSL and HSTS

    # SECURITY WARNING: Only set this to True if you are certain that all subdomains of your domain should be served exclusively via SSL.
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True # production with SSL and HSTS

    #  SECURITY WARNING: Without this, your site cannot be submitted to the browser preload list.
    SECURE_HSTS_PRELOAD = True # production with SSL and HSTS
    ```

  * Database

    ```python
        # Database
        # https://docs.djangoproject.com/en/4.0/ref/settings/#databases

        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }
    ```

* [ ] Appache User config

    ```bash
    sudo groupadd ss2dtr
    sudo useradd -m ss2dtr -g ss2dtr
    sudo usermod -a -G ss2dtr www-data
    sudo usermod -a -G ss2dtr <your_user>
    sudo usermod -a -G docker ss2dtr
    sudo usermod -a -G docker ss2dtr
    ```

    change `/etc/apache2/envvars`

    ```bash
    export APACHE_RUN_USER=ss2dtr
    # www-data
    export APACHE_RUN_GROUP=ss2dtr
    # www-data
    ```

    and check the change by this command:

    ```bash
    ps aux | egrep '(apache|httpd|rqworker|docker)'
    ```

* [ ] SSL ports config

    ```apacheconf
    SSLEngine on
    SSLCertificateFile <<SSLCertificateFile>>.pem
    SSLCertificateKeyFile <<SSLCertificateKeyFile>>.pem
    ```

* [ ] SSL

    ```bash
    openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -sha256 -days 365 -nodes
    sudo a2enmod ssl
    sudo a2enmod headers
    sudo a2ensite default-ssl
    ```

* [ ] SS2D-Docker-Tournament

    ```bash
    sudo chown :<APACHE_RUN_GROUP> -R <<SS2D-Docker-Tournament>>
    sudo chmod g+w -R <<SS2D-Docker-Tournament>>
    ```

### Setting Up SS2D-Docker-Tournament

link to the [SS2D-Docker-Tournament repo](https://github.com/RCSS-IR/SS2D-Docker-Tournament-Runner.git).

## Issues

Feel free to submit issues and enhancement requests.

Please use [Discord](https://discord.gg/yFxkCcatGe) to report specific bugs and errors.  
you can find us there:

* Alireza Sadraii : Alireza Sadraii#1141
* Nader Zare : naderzare#3664
* Omid Amini : MROA#1608

## Contributing

All contribution are welcomed. please follow these instructions to install development version of this tool on your system.

Please refer to each project's style and contribution guidelines for submitting patches and additions. In general, we follow the "fork-and-pull" Git workflow.

 1. **Fork** the repo on GitHub
 2. **Clone** the project to your own machine
 3. **Commit** changes to your own branch
 4. **Push** your work back up to your fork
 5. Submit a **Pull request** so that we can review your changes

NOTE: Be sure to merge the latest from "upstream" before making a pull request!

