= Themes =

Themes in Mumble-Django consist of two parts: A template directory and static
content. The template directory for each theme should //not// be accessible
from the browser and therefore cannot go into the same directory where the
static files (like css files and images) are in.

== Directory structure ==
    /                       Mumble-Django installation directory
    /themes/<name>/         Templates
    /htdocs/themes/<name>/  Static content

To use a theme, set the THEME variable in settings.py to the name of the theme.
This will adjust the settings so that Django first tries to load templates from
the theme's template directory, and if it does not find a template there,
proceeds to use the default (built-in) templates instead.

This means a theme should only include those templates that it actually
modifies!

== THEME_URL ==

When the THEME setting is set, Mumble-Django will automatically enable a
context processor that sets the THEME_URL template variable to the URL under
which the /htdocs/themes/<name>/ directory is served, so in order to reference
files in the static directory, template authors should always use the THEME_URL
variable as this is the most accurate way to build these URLs. THEME_URL will
always contain a trailing "/".
