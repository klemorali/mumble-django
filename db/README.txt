This file basically only exists to have HG keep the "db" directory. I
moved the DB to this subdirectory, because people keep running into
a "Cannot open database file" error which results from permissions
being set incorrectly. People mostly run "chown -R <md-dir>/*" instead
of "chown -R <md-dir>" and therefore run into these problems.

When the db is in a subdir of <md-dir>, it matches the wildcard and
will then have correct permissions.
