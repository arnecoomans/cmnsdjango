# CMNSDjango

This repository contains apps, data and scripts that support running 
CMNS django projects.


## helpers/update.sh
Update.sh is a shell script that handles updating the django project on the remote host.
It makes a git pull and based on the git output, takes the following actions
- Enable virtual env
- Installs requirements via pip
- Executes pending migrations
- Executes collectstatic
- Restarts the supervisorctl pool name 

In order for the supervisorctl restart, it will check the current directory and use the
first segment of the directory name to restart the pool. So for example, the directory
camping.cmns.nl will trigger a restart of the pool camping.


## CMNSDjango app
This app extends Django with abstract models and filter functions that are used in most
CMNS projects. By centralizing these models and reusable views, the maintenance load for
CMNS projects decreases.

### Installation instructions
- In your project settins.py:
  - Under INSTALLED_APPS
    - Add: 'cmnsdjango',
  - When using context processor
    - Under TEMPLATES, context_processors
      - Add: 'cmnsdjango.context_processors.setting_data',
  - When using multisite
    - Under MIDDLEWARE
      - Add: 'cmnsdjango.middleware.DynamicSiteMiddleware',
  - As Statics definition, use:
```
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR.joinpath('public').joinpath(STATIC_URL)
STATICFILES_DIRS = []
for app in ['cmnsdjango', ]:
    STATICFILES_DIRS.append(BASE_DIR / app / "static")
MEDIA_URL = 'files/'
MEDIA_ROOT = BASE_DIR.joinpath('public').joinpath(MEDIA_URL)
```
- Apply migrations

### Settings

Concider adding the following settings when using json_utils. Set defaults in settings.py
and overwrite the value per setting in the model definition.
```
# Default value to allow reading, suggesting and setting attributes from models via JSON API
# Use True to allow reading attributes from all models
# Use "Authenticated" to allow reading attributes only for authenticated users
# Use "Staff" to allow reading attributes only for staff members
# Use False to disallow reading attributes from all models
# When not set, it defaults to False
# Setting can be overridden in the model
ALLOW_READ_ATTRIBUTES = False 
ALLOW_SUGGEST_ATTRUBUTES = False
ALLOW_SET_ATTRIBUTES = False
```


### Usage Instructions
To extend your model with a CMNSDjango base-model:
``` from cmnsdjango.models import BaseModel, MultiSiteBaseModel ```
