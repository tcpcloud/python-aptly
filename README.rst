============
python-aptly
============

Aptly REST API client and useful tooling

.. attention:: This application is in early development stage. Every help or feedback is appreciated.

Publisher
=========

Publisher is tool for publishing latest snapshots.
It takes configuration in yaml format which defines what to publish and how.

.. code-block:: yaml
    mirror:
      aptly:
        component: main
        distributions:
          - trusty-nightly
      trusty-main:
        component: main
        distributions:
          - trusty-nightly

    repo:
      cloudlab:
        component: cloudlab
        distributions:
          - trusty-nightly
