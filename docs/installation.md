# Install CMNSDJango

To use the CMNSDjango features within your project, install the 
cmnsdjango app and load this into your config.

## Add the submodule to your django project.
In the project root:
```
git add submodule https://github.com/arnecoomans/cmnsdjango/
```

# Fetch submodule content
```
git submodule update --recursive --remote
```

- Apply migrations

## Add cmnsdjango to the Installed_apps
in your_project/settings.py:
```
INSTALLED_APPS = [
    [...]
    'cmnsdjango',
    'your_app',
]
```

### Make sure static files are available
Ensure the following lines are in your django project settings.py
```
STATIC_URL = 'static/'
TEMPLATES = [
    {
        [...]
        'DIRS': [
          BASE_DIR / 'templates',
          ],
        'APP_DIRS': True,
        [...]
     },
]
```
## Add context processor for default configuration
In order for some functionality to work, you need to add the [context 
processors](https://docs.djangoproject.com/en/5.1/ref/templates/api/#playing-with-context-objects) to your project. This offers some functionality at the
templating level that is useful when using cmnsdjango JSON handling, 
such as setting default values for loading content via Async calls.


In your settings.py, add the following line in the correct location:


your_project/settings.py:
```
TEMPLATES = [
    {
        [...]
        'OPTIONS': {
            'context_processors': [
                [...]
                'cmnsdjango.context_processors.setting_data',
            ],
            [...]
        },
    },
]
```

## When using Multisite models
  - When using multisite
    - Under MIDDLEWARE
      - Add: 'cmnsdjango.middleware.DynamicSiteMiddleware',
