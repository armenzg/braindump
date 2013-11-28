-----------------------------------
check_bouncer.py Installation Notes
-----------------------------------

As written, ``check_bouncer.py`` will run under either python 2.6 or
2.7. For various reasons, it's not likely a puppet manifest will be done
prior to python 2.7 being available. That will simplify much of the
installation.

These notes describe how the plugin was manually installed on
buildbot-master36, which only has python 2.6 at this time.

Virtual Environment Setup
-------------------------

As root::

    virtualenv-2.6 /tools/venvs/nagiosplugin
    source /tools/venvs/nagiosplugin/bin/activate

If using python 2.6, continue with::

    pip install --no-index -e hg+https://bitbucket.org/gocept/nagiosplugin@ecf310f1a9fd#egg=PACKAGE
    pip install argparse==1.2.1

If using python 2.7, you only need::

    pip install nagiosplugin==1.0.0

Plugin Installation
-------------------

Install the plugin as root::

    cd /usr/lib64/nagios/plugins &&
    curl -O https://hg.mozilla.org/build/braindump/raw-file/default/nagios-related/check_bouncer.py &&
    chmod a+x check_bouncer

Configure the plugin as root::

    cd /etc/nagios/nrpe.d
    echo >check_bouncer.cfg command[check_bouncer]=/usr/lib64/nagios/plugins/check_bouncer

Notify NRPE of the new command as root::

    service nrpe reload

Testing Installation
--------------------

As root user::

    sudo -u nagios /usr/lib64/nagios/plugins/check_bouncer
    sudo -u nagios /usr/lib64/nagios/plugins/check_nrpe -H localhost -c check_bouncer
    
Activating the Check
--------------------

File a bug asking that the following entry be added for the host::

    check_command check_nrpe!check_bouncer
