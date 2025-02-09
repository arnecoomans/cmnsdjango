# JSON Handling by cmnsdjango

Cmnsdjango introduces centralized JSON handling functionality into your
django project. It offers several views and a util-view with reusable json 
functionality, such as read, suggest and change attributes of an object.
This allows ajax-calls to fetch attributes of an object, summon an 
overlay to add an attribute to an object, display suggested attributes 
to add to an object and set or unset an attribute value.

## Installation
To be able to use the JSON functionality, you need to install the
cmnsdjango submodule into your project. Documentation of this should
be in the [/docs/installation.md](https://github.com/arnecoomans/cmnsdjango/tree/main/docs/installation.md) file.

### Add context processor to your project



### Load views into your urls.py
There are several views available for immediate use. These views do not need
to explicitly load your models, which means they are reusable and do not require
a view in your app.

The views that are available are:
|View|Description|
|---|---|
|JsonGetAttributes|Fetch attributes of your model as specified in the url parameters|
|JsonGetSuggestions|Fetch suggested related objects when adding a related object|
|JsonSetAttribute|Set an attribute to a value, create if explicitly allowed|
|GetJsonAddObjectForm|Get form to add an attribute that can be loaded into the overlay|

Alternatively, you can write your own view. In order to use the json utils, import the
json_utils into your view.
 
#### Example URL Paths
The file cmnsdjango/urls.py includes example URL paths you can use in your project.
You can also decide to import these rules into your own project.

### Load the djangocmns javascript files
Cmnsdjango offers several javascript files to handle the requests. Below the </body> 
tag of yor document, you can load the following javascript files:
|File|Description|
|---|---|
|js/cmnsdjango.js|General functions used by other functions, required before other inclusions|
|js/getAttributes.js|Fetch attribute information of an object and insert into its target container|
|js/manageAttributes.js|Set new attributes, initialize the overlay and fetch suggestions|

### Optional: Add templatetags
In order to render ajax requests with more ease, you can load the 
textmanipulation templatetags. See the [templatetags documentation](https://github.com/arnecoomans/cmnsdjango/tree/main/docs/templatetags.md)
for more information.
