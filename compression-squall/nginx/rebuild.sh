#!/bin/bash
set -x

docker rm -f gzip-nginx
docker build -t gzip-nginx .
docker run --rm --name gzip-nginx --network compression -p 80:80 -d gzip-nginx
curl -H "Accept-Encoding: gzip" --compressed http://localhost
