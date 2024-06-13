#!/bin/bash
set -e

TARGET_DIR=$1
if [ -z "$TARGET_DIR" ]
then
    echo "Usage: $0 <target_dir> <architecture>"
    exit 1
fi

ARCHITECTURE=$2
if [ -z "$ARCHITECTURE" ]
then
    echo "Usage: $0 <target_dir> <architecture>"
    exit 1
fi

# Get directory of this script
SCRIPT_DIR=$(dirname $0)

# Set up compiler
if [ -f /usr/share/cmake/toolchain.cmake ]
then
    CC=$(grep 'set(CMAKE_C_COMPILER ' /usr/share/cmake/toolchain.cmake | sed 's/.*CMAKE_C_COMPILER \([^)]*\).*/\1/')
fi

if [ -z "$CC" ]
then
    CC=gcc
fi

# Create test source
cat <<EOF >"$SCRIPT_DIR"/hello-world.cpp
#include <stdio.h>

int main() {
    printf("Hello $ARCHITECTURE packaged world!\n");
    return 0;
}
EOF

# Create test binary
mkdir -p "$SCRIPT_DIR"/build/hello-world_0.0.1-1_"$ARCHITECTURE"/usr/bin
$CC -o "$SCRIPT_DIR"/build/hello-world_0.0.1-1_"$ARCHITECTURE"/usr/bin/hello-world "$SCRIPT_DIR"/hello-world.cpp

# Create package configuration
mkdir -p "$SCRIPT_DIR"/build/hello-world_0.0.1-1_"$ARCHITECTURE"/DEBIAN
cat <<EOF >"$SCRIPT_DIR"/build/hello-world_0.0.1-1_"$ARCHITECTURE"/DEBIAN/control
Package: hello-world
Version: 0.0.1
Maintainer: example <example@example.com>
Depends: libc6
ARCHITECTURE: $ARCHITECTURE
Homepage: http://example.com
Description: A program that prints hello world
EOF

# Create test package
dpkg --build "$SCRIPT_DIR"/build/hello-world_0.0.1-1_"$ARCHITECTURE"

# Move test package to target directory
mkdir -p "$TARGET_DIR"
mv "$SCRIPT_DIR"/build/hello-world_0.0.1-1_"$ARCHITECTURE".deb "$TARGET_DIR"
