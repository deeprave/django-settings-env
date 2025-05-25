# ChangeLog

### Release 5.6.0

- Introduces a new QueuePlugin for handling queue configuration via queue URLs.
  These are parsed similarly to the cache URLs, but return a "URL" not a "LOCATION"

### Release 5.5.0

- Add overrides for is_set, is_true, is_all_set, is_any_set to respect
  the configured prefix.

### Release 5.4.2

 - Added support for redis+socket urls

### Release 5.4.0

 - Maintenance release (envex 4.2+ for nested and bar environment variable support)
 - Updated dependencies

### Release 5.3.5

- Use yarl for more robust url handling
- Update dependencies

### Release 5.3.3

- Workaround bug in publishing using the default setuptools and just use flit.

### Release 5.3.4

- Fixed a bug where the parsed port was missing in the database config

### Release 5.3.3

- Workaround bug in publishing using the default setuptools and just use flit.

### Release 5.3.0

- Unified all url parsing functions into a single module and return a ParsedUrl instead of a dictionary
- Use a standard ParsedUrl -> config conversion (instead of transform) for all plugins
- Refactored urls modules to use a plugin style architecture
  - Plugins define their own default environment variable "DATABASE_URL", "CACHE_URL", etc.
  - Plugins can override url parsing functions, if required
  - Plugins define the name of the function on the DjangoEnv object for url parsing in context
- A future version will provide a way to discover plugins in the current virtualenv, allowing for third-party plugins to be used

### Release 5.1.0

- Added "locmem" as an alias for "localmemcache" backend.
- Update dependencies
- Combined dev and test poetry groups and adjusted workflows
- Fixed a bug where repr() of a DeferredSettings instance would return a non-string (None) value

### Release 5.0.0

- Large refactoring of the codebase to improve performance and maintainability
- Removed support for queue configuration via single URL.
  The queue types that were previously supported no longer exist, and the configuration of queues varies too widely to easily support as a single url.
- refactored individual url parsers to use a common pattern with
  hooks for handling the various types of urls in separate modules, loaded only when a url of that type is used.
- Django < 4.0 is no longer supported (specifically for redis cache)
- Add support for the newer elasticsearch_dsl (or elasticsearch+dsl) search backend
- Enhanced documentation.

### Release 4.7.1

- Add support for Env(timeout) parameter (vault connection timeout)

### Release 4.7.0

- Use django core redis cache if using django >= 4.0

### Release 4.6.1

- upgrade envex to 2.2.0 for improved Vault support

### Release 4.6

- upgraded envex to 2.1.0, inherited hashicorp vault support
- cleaned up env() call behavior
- increase test coverage on core functinality
- add build & publish github action

### Release 4.5.0

- documentation cleanup
- code quality improvements

### Release 4.3.0

- fixed an issue evaluating DeferredSettings instance where __getattr__ would get skipped
- deferred values are now cached
