colon := :
$(colon) := :
TAG=latest
ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.PHONY: clean package image service

clean:
	rm -rf build dist *.egg-info

package:
	python3 setup.py bdist_wheel
	sudo apt-get install -y ruby ruby-dev rubygems build-essential
	sudo gem install -N fpm
	fpm setup.py

image:
	docker build $(ROOT_DIR) --file Dockerfile --tag effectiverange/apt-server$(:)$(TAG)

service:
	TAG=$(TAG) envsubst '$$TAG' < $(ROOT_DIR)/service/apt-server.docker.service > $(ROOT_DIR)/dist/apt-server-$(TAG:v%=%).docker.service
