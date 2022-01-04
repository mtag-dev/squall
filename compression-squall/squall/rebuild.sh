#!/bin/bash
set -x

docker rm -f squall
docker build -t squall .

docker run --rm --name squall --network compression -p 8080:8080 -d squall
curl -H "Accept-Encoding: gzip" http://localhost:8080/nginx_compression
