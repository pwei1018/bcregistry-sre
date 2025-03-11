#!/bin/bash

echo "set onepassword user"
if ! whoami &> /dev/null; then
  if [ -w /etc/passwd ]; then
    echo "onepassword:x:$(id -u):0:onepassword user:${HOME}:/sbin/nologin" >> /etc/passwd
  fi
fi

sleep 10

echo "start onnect-api"
/usr/local/bin/connect-api
