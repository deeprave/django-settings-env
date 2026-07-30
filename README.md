# django-settings-env

Django settings support built on [envex](https://pypi.org/project/envex/), with
type-aware environment values, deferred settings, and URL-based Django backend
configuration.

[![PyPI version](https://badge.fury.io/py/django-settings-env.svg)](https://badge.fury.io/py/django-settings-env)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

## Introduction

The primary functionality of this module is provided by the dependency `envex`,
which provides settings via the OS environment, `.env` files, encrypted `.env` files (since `envex` v4.0),
and optionally, HashiCorp vault (since `envex` v2.0).

## Inherited envex Features

`envex` provides a convenient type-smart interface for handling the OS environment, and therefore
configuration of any application using 12factor.net principals removing many environment-specific
variables and/or security-sensitive information from application code and source code repositories.

Settings may be sourced from .env files, encrypted .env.enc files, directly from the environment,
or from a HashiCorp vault. By default, values set in the environment take priority over those set
in .env files, and those take priority of any corresponding values stored in Vault.
This can be changed by setting `ENVEX_SOURCE` to a value such as `file`, `vault`, or any other value except `env`.

Some features not supported by other dotenv handlers (python-dotenv, etc.) are available
including expansion of template variables, which can enhance Don't Repeat Yourself.

## Installation

```shell
pip install django-settings-env
# or: uv add django-settings-env
# or: poetry add django-settings-env
```

The package supports Python 3.12–3.14 and Django 5.2–6.x. It requires
Envex 5.1 or later; installing `django-settings-env` installs the compatible
version automatically.

## Usage

This module doesn't need to be added to `INSTALLED_APPS` as it isn't a Django app, but is an add-on module available
for import.

```python
import django_settings_env
```

or

```python
from django_settings_env import Env
```

### Basic Usage

```python
from django_settings_env import Env

...
env = Env(options...)
```

By default, the env object will check both the operating system environment and any .env files in the project root for
settings; this can be customised by:

- passing readenv=False to prevent reading from any .env files
- passing a search_path to specify the location of the .env file
- adding parents=True to also search parent directories for the .env file
- adding env_file arg to override the name of the default `.env`
- passing decrypt=True and a password source to decrypt encrypted .env files

These options are all available via the `envex` module.

Wherever an Env instance is available, the environment can be accessed with env["VAR_NAME"], or env("VAR_NAME").
The latter is a convenience method that returns the value of the variable or `None` if it is not set.
A `default=<value>` keyword argument may also be used and is returned if the specified variable is not set.
The "call" syntax also has another advantage in that it can be used to set a default value if the variable is currently unset.
When assigned to a variable of the same name as the variable in the current scope, the variable does not need to be
specified, for example:

```python
from django_settings_env import Env

env = Env()
...
DEBUG = env(default=False)
```

The value of `DEBUG` is deferred until used or referenced.
The `default` keyword is required to set the default, because the first positional argument is reserved for the variable
name.

Note that this functionality only works at the same scope level as the declaration of the variable: class, module (aka
"global") or function.
It will not work for cross-scope assignments (assigning a class variable from a method, for example).
Explicitly specifying the variable name, however, will still work in this case.

## Django Settings

`django-settings-env` adds features to `envex` and specifically aims to bring full 12-factor.net compliance to
Django settings.
It will typically avoid the need to separate local/development configuration settings from production settings, as values are determined at runtime by the content of the environment, `.env` and `.env.enc` files, or values obtained from a HashiCorp vault.

By default, `Env` applies the `DJANGO_` prefix to environment-variable names as a
fallback: the plain name wins when both are set. For example, `DATABASE_URL`
takes precedence over `DJANGO_DATABASE_URL`.

Set the prefix when constructing `Env`, including an empty string to disable it:

```python
env = Env(prefix="PROJECT_")
```

The configured prefix applies to every method that accepts a variable name.
`prefix=` is not supported on individual lookup methods.

One key difference between `envex` and `django-settings-env` is that the latter will read .env files by default, and will automatically search parent directories if one is not found where initially expected. This default behaviour needs to be explicitly enabled in `envex`.

## django-settings-env API

This module provides a number of type-safe methods to help in retrieving values from the environment (including `.env`
and `.env.enc` files or from vault).
The `env.get()` method assumes a string should be returned, but other methods are available to handle other types, such
as `env.int()`, `env.bool()`, `env.float()`, `env.list()` etc.
All provide seamless conversion of the environment variable to the desired type, or return a default value if the
variable is not set.
The `env()` call syntax also provides a `type` parameter that can be used to specify the type of the variable to be
returned, which can be either a class, or the name of the class.
Only primitive types and `list` (comma separated values) are currently supported.

### Django Specific Methods

Some Django-specific functionality is included in this module, added via plugins:


| Default variable | Parser               |
| ---------------- | -------------------- |
| DATABASE_URL     | `env.database_url()` |
| CACHE_URL        | `env.cache_url()`    |
| EMAIL_URL        | `env.email_url()`    |
| SEARCH_URL       | `env.search_url()`   |
| QUEUE_URL        | `env.queue_url()`    |
| TASKS_URL        | `env.tasks_url()`    |

Each of these values can be injected into django settings via the environment, typically from a `.env(.enc)` file at the project root, or set from a variable in vault.
Individual components of these URLs can also be set, but passing the URL provides a way of setting all the required
components, including options as query parameters.

The URL includes a scheme that determines the backend class, engine, or module that handles the
corresponding functionality as documented below.
For supported URL handlers, `backend=` (or `engine=` for search) can override
the selected backend. The URL scheme must still be supported.

URLs may include options, in the form of query options, i.e. `?option=value&option2=value2` etc. that are specific to
the engine or backend being used.
Options are usually case-sensitive, and must use the same case as expected by the backend.

### Qualified schemes

Handlers support schemes with `+` qualifiers. An explicitly supported qualified
scheme is matched first; otherwise the handler falls back to the base scheme.
For example, `postgresql+psycopg://...` uses the PostgreSQL handler and
`redis+cluster://...` uses the Redis handler. Unknown qualifiers are retained
when a handler returns a URL, so configurations can pass them on to the backend.
Known qualifiers such as `smtp+ssl` and `redis+socket` retain their specialised
behaviour.

### `database_url`

- Provided by the `plugin_database` module.

Evaluate a URL in the form

```
scheme://[username:[password]@]host_or_path[:port]/name[?...options]
```

Supported schemas:

| Scheme          | Database                                    |
| --------------- | ------------------------------------------- |
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

#### Examples (snippets from settings.py)

```python
from django_settings_env import Env

env = Env()
...
DATABASES = {
    "default": env.database_url(),
    "backup": env.database_url("DATABASE_BACKUP_URL"),
}
```

### `cache_url`

- Provided by the `plugin_cache` module.

Evaluate a URL in the form

```
scheme://[username:[password]@]host_or_path[:port]/[name][?...options]
```

Supported schemas:

| Scheme      | Cache                        |
| ----------- | ---------------------------- |
| dbcache     | cache in database            |
| dummycache  | dummy cache - "no cache"     |
| filecache   | cache data in files          |
| locmem      | cache in memory              |
| locmemcache | cache in memory              |
| memcache    | memcached (python-memcached) |
| pymemcache  | memcached (pymemcache)       |
| rediscache  | redis                        |
| redis+socket| redis over a Unix socket     |
| redis       | redis                        |
| rediss      | redis (ssl connection)       |

### `email_url`

- Provided by the `plugin_email` module.

Evaluate a URL in the form

```
scheme://[username[@domain]:[password]@]host_or_path[:port]/[?...options]
```

Supported schemas:

| Scheme      | Service                       |
| ----------- | ----------------------------- |
| smtp        | smtp, no SSL                  |
| smtps       | SMTP with TLS (default port 587) |
| smtp+tls    | SMTP with TLS (default port 587) |
| smtp+ssl    | SMTP with SSL (default port 465) |
| consolemail | publish mail to console (dev) |
| filemail    | append email to file (dev)    |
| memorymail  | store emails in memory        |
| dummymail   | do-nothing email backend      |
| amazonses   | Amazon Simple Email Service   |
| amazon-ses  | Amazon Simple Email Service   |

### `search_url`

- Provided by the `plugin_search` module.

Evaluate a URL in the form

```
scheme://[username:[password]@]host_or_path[:port]/[index]
```

Supported schemas:

| Scheme            | Engine                                       |
| ----------------- | -------------------------------------------- |
| elasticsearch     | elasticsearch (django-haystack)              |
| elasticsearch2    | elasticsearch2 (django-haystack)             |
| elasticsearch+dsl | elasticsearch-dsl                            |
| elasticsearch-dsl | elasticsearch-dsl                            |
| solr              | Apache solr (django-haystack)                |
| whoosh            | Whoosh search engine (pure python, haystack) |
| xapian            | Xapian search engine (haystack)              |
| simple            | Simple search engine (haystack)              |

Note that django-haystack may require many additional settings not supported by this module.
`elasticsearch-dsl` is recommended as a suitable replacement, and in general integrates well with Django's ORM,
providing the ability to easily relate ES documents+indexes to Django models.
The DSL version also supports more contemporary versions of Elasticsearch and is well maintained.

### `queue_url`

- Provided by the `plugin_queue` module.

Returns a Django cache-style queue configuration with `BACKEND` and `URL`.
Supported schemes are `pymemqueue`, `redisqueue`, `redis`, `rediss`, and
`redis+socket`. Redis URLs using `unix` as the host are converted to Unix-socket
URLs.

### `tasks_url`

- Provided by the `plugin_tasks` module.

Returns a Django task backend configuration for Django's built-in `dummy` and
`immediate` task backends, available in Django 6.0 or later. Additional task
transports require a dedicated external integration. Its default environment
variable is `TASKS_URL`; pass a variable name to `env.tasks_url()` to use
another value.

## Django Class Settings

Support for the [`django-class-settings`](https://pypi.org/project/django-class-settings/) module is dynamically added to the env handler, allowing a much simplified use within a class_settings.Settings class, e.g.:

```python
from django_settings_env import Env
# noinspection PyUnresolvedReferences
from class_settings import Settings

env = Env(prefix='DJANGO_')  # redundant, this is the default


class MySettings(Settings):
    MYSETTING = env()
```

This usage will look for 'MYSETTING' or 'DJANGO_MYSETTING' in the environment and lazily
assign it to the MYSETTING value for the settings class.


## Connection to Vault

Connecting to vault is optional, and handled by the `envex` module.
The connection is determined by the presence of VAULT_ADDR in the environment.
It can't be set from a `.env` as typically the connection to Vault determined when the env object is instantiated,
before it scans and reads any `.env` files.

> :warning: If $VAULT_ADDR is set but the vault server is not running or is unavailable, there may be a considerable
> startup delay until the connection times out.

In addition, $VAULT_TOKEN is required to be set in the environment to authenticate with the vault
server.
Other environment variables may also be required, depending on the vault configuration.

| Variable          | Description                                         |
| ----------------- | --------------------------------------------------- |
| VAULT_ADDR        | URL of the vault server                             |
| VAULT_TOKEN       | Token to authenticate with the vault server         |
| VAULT_CACERT      | Path to the CA certificate for the vault server     |
| VAULT_SKIP_VERIFY | Skip verification of the vault server certificate   |
| VAULT_CLIENT_CERT | Path to the client certificate for the vault server |
| VAULT_CLIENT_KEY  | Path to the client key for the vault server         |
| VAULT_TIMEOUT     | Timeout for the vault connection (in seconds)       |

While setting the `VAULT_TIMEOUT` item can reduce the startup delay if the vault server is not available, the vault
module retries multiple times before giving up, so the delay may still be considerable.
This variable is provided to *increase* the connection timeout should the default of 5 seconds be insufficient to
successfully establish the connection.
Reducing it even further is not recommended.

VAULT_CACERT is useful when running vault with TLS is enabled (**highly recommended**), and the certificate is not
signed by a recognised Certificate Authority, i.e. self-signed or an internal CA.
Alternatively, `VAULT_SKIP_VERIFY=true` in the environment will disable verification of the vault server certificate (*
*not recommended**).

VAULT_CLIENT_CERT and VAULT_CLIENT_KEY are optional and are only required if the vault server requires client
certificates.
If used, both variables must be set and provide valid paths to the client certificate and key.

The vault store contains a single object containing all values in a dictionary format, and is cached by default.
The cache is used to return individual values by key (same key as the environment variable) with the assumption that the
vault secrets remain unchanged during the application runtime.
Consequently, any changes to vault require an application restart, so it is wise to consider which items to put in vault
and which to put in the environment.
It is recommended to only place items in the vault that contain secrets or are otherwise sensitive.
