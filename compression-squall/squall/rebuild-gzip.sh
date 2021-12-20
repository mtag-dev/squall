#!/bin/bash
set -x

docker rm -f gzip-squall
docker build -f Dockerfile-gzip -t gzip-squall .

docker run --rm --name gzip-squall --network compression -p 8081:8081 -d gzip-squall
curl -H "Accept-Encoding: gzip" --compressed http://localhost:8081/squall_compression
