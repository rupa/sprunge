Command line pastebin for google app-engine, in use at [sprunge.us](http://sprunge.us).

Requirements:

* [pygments](http://pygments.org/). currently using version 1.6.
* [cloudstorage](https://developers.google.com/appengine/docs/python/googlecloudstorageclient/download).

Version 2:

* Pretty much a complete rewrite, should be transparent to users.
* Sprunge contents are stored in the Blobstore (actually the Cloud Storage
  "default bucket") rather than the Datastore. This gives us more room.
* Existing sprunges are migrated on demand.

Version 1:

* [For reference](https://github.com/rupa/sprunge/releases/tag/v1).

Licensed under the WTFPL.
