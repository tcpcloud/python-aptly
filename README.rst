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
