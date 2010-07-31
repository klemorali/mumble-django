#!/bin/bash

# Create a new release of Mumble-Django.

set -e
set -u

export HGPLAIN=t

BASEDIR=`hg root`
PYWEB="${BASEDIR}/pyweb"
LASTTAG=`hg tags | grep -v tip | head -n1 | cut -d' ' -f1`

cd "${PYWEB}"

echo "Updating djExtDirect."
wget -nv -N 'http://bitbucket.org/Svedrin/djextdirect/raw/tip/djextdirect.py'
if hg status djextdirect.py | grep djextdirect.py > /dev/null; then
    # looks like wget changed the file
    hg commit djextdirect.py -m "Update djExtDirect"
fi

VERSIONSTR=`python -c 'import mumble; print mumble.version_str'`

echo
echo "Current version is ${VERSIONSTR}."

if hg tags | grep "${VERSIONSTR}" > /dev/null; then
    echo "Warning: Version string in Mumble module has not been updated."
    echo "         Running vi so you can fix it in three, two, one."
    sleep 3
    MODFILE="${PYWEB}/mumble/__init__.py"
    vi "$MODFILE" -c '/version ='
    hg commit "$MODFILE" -m 'Bump mumble module version'
fi

VERSIONSTR=`python -c 'import mumble; print mumble.version_str'`

SETUPVER=`grep 'version=' setup_mucli.py | cut '-d"' -f2`
if [ "v${SETUPVER}" != "${VERSIONSTR}" ]; then
    echo "Warning: Version string in setup_mucli.py has not been updated."
    echo "         Running vi so you can fix it in three, two, one."
    sleep 3
    MODFILE="${PYWEB}/setup_mucli.py"
    vi "$MODFILE" -c '/version='
    hg commit "$MODFILE" -m 'Bump version in setup_mucli.py'
fi

HISTFILE=`tempfile`
hg log -r "${LASTTAG}:tip" > "${HISTFILE}"
vi -p "${HISTFILE}" "${BASEDIR}/CHANGELOG"
rm "${HISTFILE}"

echo "New version will be tagged ${VERSIONSTR}. If this is correct, hit enter to continue."
read

echo hg commit "${BASEDIR}/CHANGELOG" -m "Releasing ${VERSIONSTR}."
echo hg tag "${VERSIONSTR}"
echo hg push

echo "You successfully released ${VERSIONSTR}!"

