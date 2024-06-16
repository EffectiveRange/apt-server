colon := :
$(colon) := :
TAG=latest
PACKAGE_ARCHS=armhf,arm64,amd64
ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.PHONY: clean package image service

clean:
	rm -rf build dist *.egg-info

package:
	apt-get update && apt-get install -y build-essential debhelper devscripts equivs dh-virtualenv python3-virtualenv
	dpkg-buildpackage -us -ui -uc --buildinfo-option=-udist --buildinfo-option=-Odist/apt-server.buildinfo --changes-option=-udist --changes-option=-Odist/apt-server.changes
	rm dist/*.buildinfo dist/*.changes dist/*.dsc dist/*_*.tar.gz

image:
	docker build $(ROOT_DIR) --file Dockerfile --tag effectiverange/apt-server$(:)$(TAG) --build-arg PACKAGE_ARCHS=$(PACKAGE_ARCHS)

service:
	@cat $(ROOT_DIR)/service/apt-server.docker.service | TAG=$(TAG) envsubst > $(ROOT_DIR)/dist/apt-server-$(TAG).docker.service
