Blender ID addon
================

This addon allows you to authenticate your Blender with your
[Blender ID](https://www.blender.org/id/) account. This authentication
can then be used by other addons, such as the
[Blender Cloud addon](https://developer.blender.org/diffusion/BCA/)

Building & Installation
-----------------------

* To build the addon, run `python setup.py bdist`
* If you don't have one already, sign up for an account at
  the [Blender ID site](https://www.blender.org/id/).
* Install the addon from Blender (User Preferences → Addons → Install
  from file...) by pointing it to `dist/blender_id*.addon.zip`.
* Enable the addon in User Preferences → Addons → System.
* Log in!

NOTE: The addon requires HTTPS connections, and thus is dependent on
[D1845](https://developer.blender.org/D1845). You can do either of
these:

* Build Blender yourself
* Get a recent copy from the buildbot
* Copy certificate authority certificate PEM file to
  `blender/2.77/python/lib/python3.5/site-packages/requests/cacert.pem`.
  You can use the same file from your local requests installation, or
  use `/etc/ssl/certs/ca-certificates.crt`.

