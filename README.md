metricdock
==========

Receives metrics in JSON via HTTP and stores them in Whisper databases.

Running on Heroku
-----------------
Compile the slug using both python and redis buildpacks:
heroku config:set BUILDPACK\_URL=https://github.com/ddollar/heroku-buildpack-multi.git

Tell the app about its publicly-reachable name:
heroku config:set PUBLIC\_NAME=metrics1.example.com

Set the following based on your Swift endpoint:
heroku config:set SWIFT\_API\_KEY=0123456789ABCDEF
heroku config:set SWIFT\_AUTHURL=https://objects.example.com/auth
heroku config:set SWIFT\_CONTAINER=metrics1
heroku config:set SWIFT\_USERNAME=metricdock:whisper
