metricdock
==========

Receives metrics in JSON via HTTP and stores them in Whisper databases.

Overview
--------
In an effort to avoid losing metrics when a dock server restarts:
+ When a metric is received, it's written to Whisper and a redis "latest" queue
+ At startup, a baseline archive of Whisper is retrieved from persistent storage (e.g. a Swift service)
+ Fellow dock servers are queried for their "latest" queues
+ The other servers respond by sending all metrics stored in their "latest" queues
+ The received metrics are saved to Whisper; duplicate metrics simply overwrite each other

The API is documented with examples in the docs/ folder.

Running on Heroku
-----------------
Compile the slug using both python and redis buildpacks:
```shell
heroku config:set BUILDPACK_URL=https://github.com/ddollar/heroku-buildpack-multi.git
```

Tell the app about its publicly-reachable name:
```shell
heroku config:set PUBLIC_NAME=metrics1.example.com
```

Set the following based on your Swift endpoint:
```shell
heroku config:set SWIFT_API_KEY=0123456789ABCDEF
heroku config:set SWIFT_AUTHURL=https://objects.example.com/auth
heroku config:set SWIFT_CONTAINER=metrics1
heroku config:set SWIFT_USERNAME=metricdock:whisper
```

To enable redundancy, tell the app about other dock servers:
```shell
heroku config:set DOCKS=http://metrics2.example.com,http://metrics3.example.com
```

Redundancy
----------
Since group membership is currently manually controlled via the 'DOCKS'
envvar, modifying group membership (e.g. adding a new server) involves making
the change on a single dock, allowing it time to restart and sync, and then
proceeding to make the change on another dock.
