colon := :
$(colon) := :
IMG_TAG=latest
PACKAGE_ARCHS=armhf,arm64,amd64
ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.PHONY: arm64 amd64 package build-image create-service apt-server-arm64-image apt-server-amd64-image apt-server-arm64-service apt-server-amd64-service

arm64:
	$(eval ARCH=arm64)
	$(eval DOCKER_ARCH=arm64v8)

amd64:
	$(eval ARCH=amd64)
	$(eval DOCKER_ARCH=$(ARCH))

clean:
	rm -rf build dist *.egg-info

package:
	apt-get update && apt-get install -y build-essential debhelper devscripts equivs dh-virtualenv python3-virtualenv
	dpkg-buildpackage -us -ui -uc --buildinfo-option=-udist --buildinfo-option=-Odist/apt-server.buildinfo --changes-option=-udist --changes-option=-Odist/apt-server.changes

build-image:
	docker build $(ROOT_DIR) --file Dockerfile --tag effectiverange/apt-server$(:)$(IMG_TAG) --build-arg --build-arg PACKAGE_ARCHS=$(PACKAGE_ARCHS)

apt-server-arm64-image: arm64 build-image

apt-server-amd64-image: amd64 build-image
