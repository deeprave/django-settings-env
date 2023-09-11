# django-settings-env

12-factor.net settings environment handler for Django settings.

[![PyPI version](https://badge.fury.io/py/django-settings-env.svg)](https://badge.fury.io/py/django-settings-env)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

## [envex](https://pypi.org/project/envex/)

[![PyPI version](https://badge.fury.io/py/envex.svg)](https://badge.fury.io/py/envex)

The primary functionality of this module is provided by the dependency `envex`,
which provides settings via the OS environment, `.env` files and, optionally,
HashiCorp vault (since `envex` v2.0).

`envex` provides a convenient type-smart interface for handling the environment, and therefore
configuration of any application using 12factor.net principals removing many environment-specific
variables and security sensitive information from application code.
Settings may be set in .env files, directly within the environment, or in HashiCorp vault.

By default, values set in the environment take priority over those set in .env files, and
those take priority of any corresponding values stored in Vault.
This can be changed by setting `$ENVEX_SOURCE` or any value other than `env`.

Some features not supported by other dotenv handlers (python-dotenv, etc.) are available
including expansion of template variables, which is very useful for DRY.

## Django Settings

By default, the Django Env class can apply a given prefix (default is "DJANGO_")
to environment variables names, but will only be used in that form if the raw (no prefix)
variable name is not already set in the environment.
To change the prefix including setting it to an empty string, pass the prefix= kwarg to `Env()`.

One key difference between `envex` and `django-settings-env` is that the latter will read .env files
by default, and will automatically search parent directories if one is not found where initially expected.
This behaviour needs to be explicitly enabled in `envex`.

Some django specific methods included in this module are URL parsers for:

| Default Var  | Parser               |
|--------------|----------------------|
| DATABASE_URL | `env.database_url()` |
| CACHE_URL    | `env.cache_url()`    |
| EMAIL_URL    | `env.email_url()`    |
| SEARCH_URL   | `env.search_url()`   |
| QUEUE_URL    | `env.queue_url()`    |

each of which can be injected into django settings via the environment, typically
from a .env file at the project root, or set from a variable in vault.

The name of the file and paths searched is fully customisable.

The url specified includes a schema that determines the "backend" class or module
that handles the corresponding functionality as documented below.

### `database_url`

Evaluate a URL in the form

```
schema://[username:[password]@]host_or_path[:port]/name
```

Schemas:

| Scheme          | Database                                    |
|-----------------|---------------------------------------------|
| postgres        | Postgres (psycopg2 or psycopg)              |
| postgresql      | Postgres (psycopg2 or psycopg)              |
| psql            | Postgres (psycopg2 or psycopg)              |
| pgsql           | Postgres (psycopg2 or psycopg)              |
| postgis         | Postgres (psycopg2 or psycopg) + PostGIS    |
| mysql           | MySql (mysqlclient)                         |
| mysql2          | MySql (mysqlclient)                         |
| mysql-connector | MySql (mysql-connector)                     |
| mysqlgis        | MySql (mysqlclient) using GIS extensions    |
| mssql           | SqlServer (sql_server.pyodbc)               |
| oracle          | Oracle (cx_Oracle)                          |
| pyodbc          | ODBC (pyodbc)                               |
| redshift        | Amazon Redshift                             |
| spatialite      | Sqlite with spatial extensions (spatialite) |
| sqlite          | Sqlite                                      |
| ldap            | django-ldap                                 |

### `cache_url`

Evaluate a URL in the form

```
schema://[username:[password]@]host_or_path[:port]/[name]
```

Schemas:

| Scheme      | Cache                        |
|-------------|------------------------------|
| dbcache     | cache in database            |
| dummycache  | dummy cache - "no cache"     |
| filecache   | cache data in files          |
| locmemcache | cache in memory              |
| memcache    | memcached (python-memcached) |
| pymemcache  | memcached (pymemcache)       |
| rediscache  | redis (django-redis)         |
| redis       | redis (django-redis)         |

### `email_url`

Evaluate a URL in the form

```
schema://[username[@domain]:[password]@]host_or_path[:port]/
```

Schemas:

| Scheme      | Service                       |
|-------------|-------------------------------|
| smtp        | smtp, no SSL                  |
| smtps       | smtp over SSL                 |
| smtp+tls    | smtp over SSL                 |
| smtp+ssl    | smtp over SSL                 |
| consolemail | publish mail to console (dev) |
| filemail    | append email to file (dev)    |
| memorymail  | store emails in memory        |
| dummymail   | do-nothing email backend      |
| amazonses   | Amazon Wimple Email Service   |
| amazon-ses  | Amazon Wimple Email Service   |

### `search_url`

Evaluate a URL in the form

```
schema://[username:[password]@]host_or_path[:port]/[index]
```

Schemas:

| Scheme         | Engine                                       |
|----------------|----------------------------------------------|
| elasticsearch  | elasticsearch (django-haystack)              |
| elasticsearch2 | elasticsearch2 (django-haystack)             |
| solr           | Apache solr (django-haystack)                |
| whoosh         | Whoosh search engine (pure python, haystack) |
| xapian         | Xapian search engine (haystack)              |
| simple         | Simple search engine (haystack)              |

### `queue_url`

Evaluate a URL in the form

```
schema://[username:[password]@]host_or_path[:port]/[queue]
```

Schemas:

| Scheme     | Engine               |
|------------|----------------------|
| rabbitmq   | RabbitMQ             |
| redis      | Redis                |
| amazonsqs  | Amazon SQS           |
| amazon-sqs | alias for Amazon SQS |


## Django Class Settings


Support for the [`django-class-settings`](https://pypi.org/project/django-class-settings/) module is added to the env handler, allowing a much simplified use withing a class_settings.Settings class, e.g.:

```python
from django_settings_env import Env
# noinspection PyUnresolvedReferences
from class_settings import Settings

env = Env(prefix='DJANGO_')


class MySettings(Settings):
    MYSETTING = env()
```

This usage will look for 'MYSETTING' or 'DJANGO_MYSETTING' in the environment and lazily
assign it to the MYSETTING value for the settings class.

> :warning: The functional form of env() is now available even if `django-class-settings` is not
> used or installed and is available at the settings module level.


## Vault Support

See the [envex](https://pypi.org/envex) documentation for details on how to configure this package with HashiCorp Vault.
