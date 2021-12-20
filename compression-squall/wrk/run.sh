#!/bin/bash
set -x

docker run --rm --network compression czerasz/wrk-json \
    wrk http://gzip-nginx/nginx_compression -d15s -t4 -c64


docker run --rm --network compression czerasz/wrk-json \
    wrk http://gzip-nginx/squall_compression -d15s -t4 -c64


#docker run --rm --network compression -v $(pwd):/scripts czerasz/wrk-json \
#    wrk http://localhost/nginx_compression -d15s -t4 -c64
#handler.lua
#benchmark-framework-scenario:
#	@echo "\nRun fixture $(FIXTURE) [$(FRAMEWORK) $(SCENARIO)]\n"
#	@docker run --rm --network bench \
#			-e FRAMEWORK=$(FRAMEWORK) -e FILENAME=$(FILENAME) -e FIXTURE=$(FIXTURE) -e SCENARIO=$(SCENARIO)  \
#			-v $(CURDIR)/fixtures:/fixtures \
#			-v $(CURDIR)/results:/results \
#			-v $(CURDIR)/wrk:/scripts \
#			--sysctl net.core.somaxconn=4096 \
#			czerasz/wrk-json \
#			wrk http://benchmark:8080 -d$(DURATION) -t$(THREADS) -c$(CONCURRENT) -s /scripts/process.lua
#	@echo "\nFinish [$(FRAMEWORK) $(SCENARIO)]\n"