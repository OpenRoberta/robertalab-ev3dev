# intro #
A connector to use a LEGO Mindstorm ev3 running the ev3dev firmware
(http://www.ev3dev.org) from the Open Roberta lab (http://lab.open-roberta.org).
This is now included by default with ev3dev images (Thanks @dlech), but it is
prevented from running by default, so you do have to enable it once:

    sudo systemctl unmask openrobertalab.service
    sudo systemctl start openrobertalab.service

After running the commands above, it will start automatically after a reboot.
You can turn it back off by running:

    sudo systemctl stop openrobertalab.service
    sudo systemctl mask openrobertalab.service

If the ``openrobertalab`` package is installed and the service is running, the
'Open Roberta' menu item in brickman will allow you to connect to an Open
Roberta server.

# build status #

* master [![master](https://travis-ci.org/OpenRoberta/robertalab-ev3dev.svg?branch=master)](https://travis-ci.org/OpenRoberta/robertalab-ev3dev/builds)
* develop [![develop](https://travis-ci.org/OpenRoberta/robertalab-ev3dev.svg?branch=develop)](https://travis-ci.org/OpenRoberta/robertalab-ev3dev/builds)

# development #
## prerequisites ##
python-ev3dev
python-bluez
python-dbus
python-gobject

## dist ##

    VERSION="1.3.2" python setup.py sdist

Now you can also build a debian package using ``debuild`` or 
``debuild -us -us``. The new package will be in the parent folder.

## upload to ev3 ##
The easiest is to upload the debian package and install it.

    scp ../openrobertalab_1.3.2-1_all.deb root@ev3dev.local:/tmp/
    ssh root@ev3dev.local "dpkg --install /tmp/openrobertalab_1.3.2-1_all.deb"

## configuration ##
The brickman ui will store configuration data under /etc/openroberta.conf. All
configuration can be edited from the UI. If there is a need to manully change
the config, it is adviced to stop brickman.

## Testing ##
``python -m unittest roberta.test_lab`` or ``nosetests``.
The test require ``python-httpretty``, but run without ``python-ev3dev``.

