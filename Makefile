colon := :
$(colon) := :
IMG_TAG=latest
PACKAGE_ARCHS=armhf,arm64,amd64
ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.PHONY: clean package build-image

clean:
	rm -rf build dist *.egg-info

package:
	apt-get update && apt-get install -y build-essential debhelper devscripts equivs dh-virtualenv python3-virtualenv
	dpkg-buildpackage -us -ui -uc --buildinfo-option=-udist --buildinfo-option=-Odist/apt-server.buildinfo --changes-option=-udist --changes-option=-Odist/apt-server.changes

build-image:
	docker build $(ROOT_DIR) --file Dockerfile --tag effectiverange/apt-server$(:)$(IMG_TAG) --build-arg PACKAGE_ARCHS=$(PACKAGE_ARCHS)
