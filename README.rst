============
Scrap Logger
============

A pile of useful things I've worked out in various projects.  Collected them into a reusable module.

Handlers
----

Dated File Handler
^^^^

Handler for logging to a set of files, which switches from one file
to the next when the current date/time changes sufficiently.

This handler came about in a Django project and had it starting a new file each day.

Tests
====

Runs tests as:

::

    python -m unittest

Unrelated to this module
====

Helpful `rst cheatsheet`_.

.. _rst cheatsheet: https://github.com/ralsina/rst-cheatsheet/blob/master/rst-cheatsheet.rst
