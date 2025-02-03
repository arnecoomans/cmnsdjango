# CMNSDjango

This repository contains apps, data and scripts that support running 
CMNS django projects.

## Helpers
Helper scripts make your django project more manageble. Read about helpers at
[docs/helpers.md](https://github.com/arnecoomans/cmnsdjango/tree/main/docs)

## CMNSDjango app
This app extends Django with abstract models and filter functions that are used in most
CMNS projects. By centralizing these models and reusable views, the maintenance load for
CMNS projects decreases.

### Installation instructions
Read installation documentation in [/docs](https://github.com/arnecoomans/cmnsdjango/tree/main/docs).

### Usage Instructions
To extend your model with a CMNSDjango base-model:
``` from cmnsdjango.models import BaseModel, MultiSiteBaseModel ```
