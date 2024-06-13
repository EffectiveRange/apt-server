colon := :
$(colon) := :
IMG_TAG=latest
ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.PHONY: arm64 amd64 package build-image create-service apt-server-arm64-image apt-server-amd64-image apt-server-arm64-service apt-server-amd64-service

arm64:
	$(eval ARCH=arm64)
	$(eval DOCKER_ARCH=arm64v8)

amd64:
	$(eval ARCH=amd64)
	$(eval DOCKER_ARCH=$(ARCH))

package:
	apt-get update && apt-get install -y build-essential debhelper devscripts equivs dh-virtualenv python3-virtualenv
	dpkg-buildpackage -us -ui -uc --buildinfo-option=-udist --buildinfo-option=-Odist/apt-server.buildinfo --changes-option=-udist --changes-option=-Odist/apt-server.changes

build-image:
	docker build $(ROOT_DIR) --file Dockerfile --tag effectiverange/er-apt-server-$(ARCH)$(:)$(IMG_TAG) --build-arg SERVER_ARCH=$(DOCKER_ARCH) --build-arg CLIENT_ARCH=armhf

create-service:
	@cat $(ROOT_DIR)/service/apt-server.service.template | TAG=$(IMG_TAG) ARCH=$(ARCH) DOCKER_ARCH=$(DOCKER_ARCH) envsubst

apt-server-arm64-image: arm64 package build-image

apt-server-amd64-image: amd64 package build-image

apt-server-arm64-service: arm64 create-service

apt-server-amd64-service: amd64 create-service
