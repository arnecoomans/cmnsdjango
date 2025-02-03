# Templatetags 

# Installation
Include the dedired template tag in your projects settings.py:
```
TEMPLATES = [
    {
        [...]
        'OPTIONS': {
            'builtins': [
                [...]
                'cmnsdjango.templatetags.filter_by_visibility',
                'cmnsdjango.templatetags.markdown',
                'cmnsdjango.templatetags.query_filters',
                'cmnsdjango.templatetags.textmanipulation',
            ]
        },
    },
]
```

## Filter by visibility

## Markdown
Apply markdown filter to a value. 
Example usage: {{ textarea|markdown|safe }}
Add |safe to ensure rendered markdown is not html encoded.

## Query filters
Take the current request query and add or remove or change a value in
query settings. Example usage: 
- {% url 'yourapp:yoururl' %}{% update_query_params request add=object.slug to='category' active_filters=active_filters %}

## Text manipulation
Default text manipulation filters
### Replace
Replace a part of a string inside a string. 
Example usage: {{ "aaa"|replace:"a|b" }}
### Highlight
Highlight a part in a string case-insensitive. 
Example usage: {{ "First Lastname"|highlight:"last" }}
### Split
Split a string into a list by delimiter. 
Example usage: {% with value="a,b,c" %}{{ value|split:"," }}{% endwidth %}