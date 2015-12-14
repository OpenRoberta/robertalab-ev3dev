# intro #
A connector to use a LEGO Mindstorm ev3 running the ev3dev firmware
(http://www.ev3dev.org) from the Open Roberta lab (http://lab.open-roberta.org).

Build status:

* master [![master](https://travis-ci.org/OpenRoberta/robertalab-ev3dev.svg?branch=master)](https://travis-ci.org/OpenRoberta/robertalab-ev3dev/builds)
* develop [![develop](https://travis-ci.org/OpenRoberta/robertalab-ev3dev.svg?branch=develop)](https://travis-ci.org/OpenRoberta/robertalab-ev3dev/builds)

## prerequisites ##
python-ev3dev
python-bluez
python-dbus

## dist ##
``VERSION="1.3.2" python setup.py sdist``

Now you can also build a debian package using:
``./package-deb.sh dist/openrobertalab-1.3.2.tar.gz``

## upload to ev3 ##
The easiest is to upload the debian package and install it.
``
scp <temp>/openrobertalab_1.3.2-1_all.deb root@ev3dev.local:/tmp/
ssh root@ev3dev.local "dpkg --install /tmp/openrobertalab_1.3.2-1_all.deb"
``

## start it ##
As of now, you still need an unreleased version of brickman from git:
https://github.com/ev3dev/brickman

If the 'openrobertalab' package is installed and the service is running, the
'Open Roberta' menu item in brickman will allow you to connect to an Open
Roberta server.

## configuration ##
The brickman ui will store configuration data under /etc/openroberta.conf. All
configuration can be edited from the UI. If there is a need to manully change
the config, it is adviced to stop brickman.

## Testing ##
python -m unittest tests.test_openrobertalab
The test requires python-httpretty.
