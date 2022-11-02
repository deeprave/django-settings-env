-------------------
django-settings-env
-------------------
12-factor.net settings environment handler for Django

envex
---------

The functionality outlined in this section is derived from the dependent package
`envex`, the docs for which are partially repeated below.

Skip to the Django Support section for functionality added by this extension.

`envex` provides a convenient type-smart interface for handling the environment, and therefore
configuration of any application using 12factor.net principals removing many environment specific
variables and security sensitive information from application code.

This module provides some features not supported by other dotenv handlers
(python-dotenv, etc.) including expansion of template variables which is very useful
for DRY.

More detailed info can be found in the `envex` README.


Django Support
--------------

By default, the Env class provided by this module can apply a given prefix (default "DJANGO_")
to environment variables names, but will only be used in that form if the raw (unprefixed)
variable name is not set in the environment. To change the prefix including setting it to
an empty string, pass the prefix= kwarg to `Env.__init__`.

Some django specific methods included in this module are URL parsers for:

| Default Var    | Parser
|----------------|----------------------- 
| DATABASE_URL   | `env.database_url()`
| CACHE_URL      | `env.cache_url()`
| EMAIL_URL      | `env.email_url()`
| SEARCH_URL     | `env.search_url()`
| QUEUE_URL      | `env.queue_url()`

each of which can be injected into django settings via the environment, typically
from a .env file at the project root.

The name of the file and paths searched is fully customisable.

The url specified includes a schema that determines the "backend" class or module
that handles the corresponding functionality as documented below.

## `database_url`
Evaluates a URL in the form 
```
schema://[username:[password]@]host_or_path[:port]/name
```
Schemas:

| Scheme          | Database
|-----------------|----------------------
| postgres        | Postgres (psycopg2)
| postgresql      | Postgres (psycopg2)
| psql            | Postgres (psycopg2)
| pgsql           | Postgres (psycopg2)
| postgis         | Postgres (psycopg2) using PostGIS extensions
| mysql           | MySql (mysqlclient) 
| mysql2          | MySql (mysqlclient)
| mysql-connector | MySql (mysql-connector)
| mysqlgis        | MySql (mysqlclient) using GIS extensions
| mssql           | SqlServer (sql_server.pyodbc)
| oracle          | Oracle (cx_Oracle)
| pyodbc          | ODBC (pyodbc)
| redshift        | Amazon Redshift
| spatialite      | Sqlite with spatial extensions (spatialite)
| sqlite          | Sqlite
| ldap            | django-ldap

## `cache_url`
Evaluates a URL in the form
```
schema://[username:[password]@]host_or_path[:port]/[name]
```
Schemas:

| Scheme          | Cache
|-----------------|----------------------
| dbcache         | cache in database
| dummycache      | dummy cache - "no cache" 
| filecache       | cache data in files
| locmemcache     | cache in memory
| memcache        | memcached (python-memcached)
| pymemcache      | memcached (pymemcache)
| rediscache      | redis (django-redis)
| redis           | redis (django-redis)

## `email_url`
Evaluates a URL in the form
```
schema://[username[@domain]:[password]@]host_or_path[:port]/
```
Schemas:

| Scheme          | Service
|-----------------|----------------------
| smtp            | smtp, no SSL
| smtps           | smtp over SSL
| smtp+tls        | smtp over SSL
| smtp+ssl        | smtp over SSL
| consolemail     | publish mail to console (dev)
| filemail        | append email to file (dev)
| memorymail      | store emails in memory
| dummymail       | do-nothing email backend
| amazonses       | Amazon Wimple Email Service
| amazon-ses      | Amazon Wimple Email Service

## `search_url`
Evaluates a URL in the form
```
schema://[username:[password]@]host_or_path[:port]/[index]
```
Schemas:

| Scheme          | Engine
|-----------------|----------------------
| elasticsearch   | elasticsearch (django-haystack)
| elasticsearch2  | elasticsearch2 (django-haystack)
| solr            | Apache solr (django-haystack)
| whoosh          | Whoosh search engine (pure python, haystack)
| xapian          | Xapian search engine (haystack)
| simple          | Simple search engine (haystack)

## `queue_url`
Evaluates a URL in the form
```
schema://[username:[password]@]host_or_path[:port]/[queue]
```
Schemas:

| Scheme          | Engine
|-----------------|----------------------
| rabbitmq        | RabbitMQ
| redis           | Redis
| amazonsqs       | Amazon SQS
| amazon-sqs      | alias for Amazon SQS


Django Class Settings
---------------------

Support for the `django-class-settings` module is added to the env handler, allowing
a much simplified use withing a class_settings.Settings class, e.g.:

```python
from django_settings_env import Env
from class_settings import Settings

env = Env(prefix='DJANGO_')

class MySettings(Settings):
    MYSETTING = env()
```
This usage will look for 'MYSETTING' or 'DJANGO_MYSETTNG' in the environment and lazily
assign it to the MYSETTING value for the settings class.

> :warning: The functional form of env() is now available even if django class settings is not
used or installed.

