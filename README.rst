============
python-aptly
============

Aptly REST API client and useful tooling

.. attention:: This application is in early development stage. Every help or feedback is appreciated.

Publisher
=========

Publisher is tool for publishing latest snapshots.
It takes configuration in yaml format which defines what to publish and how.

Publisher expects snapshots in format ``<name>-<timestamp>``.

Features
--------

- create publish from latest snapshots
- promote publish

  - use it's snapshots to create or update another publish (eg. testing ->
    stable)

- cleanup unused snapshots

Example configuration
---------------------

.. code-block:: yaml

    mirror:
      aptly:
        component: main
        distributions:
          - trusty-nightly
      trusty-main:
        component: main
        distributions:
          - nightly/trusty

    repo:
      cloudlab:
        component: cloudlab
        distributions:
          - nightly/trusty
          - testing/trusty

Configuration above will create two publishes:

- ``nightly/trusty`` with component cloudlab and main (created snapshot
  main-`<timestamp>` by merging snapshots aptly-`<timestamp>` and
  trusty-main-`<timestamp>` snapshots)
- ``nightly/trusty`` with component cloudlab

Build
=====

You can install directly using ``setup.py`` or build Debian package with eg.:

::

  dpkg-buildpackage -uc -us

Read more
=========

For more informations, see ``aptly-publisher --help`` or man page.

::

  man man/aptly-publisher.1

Known issues
============

- determine source snapshots correctly
  (`#271 <https://github.com/smira/aptly/issues/271>`_)
- cleanup merged snapshots before cleaning up source ones
