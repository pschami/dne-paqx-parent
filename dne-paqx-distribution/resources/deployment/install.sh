#!/bin/bash
#
# Copyright (c) 2017 Dell Inc. or its subsidiaries.  All Rights Reserved.
# Dell EMC Confidential/Proprietary Information
#

RETVAL=0

echo "Loading Dell Inc. DNE PAQX docker image."

docker load -i IMAGE_NAME_STANDIN.tar

#if -s, skip running the docker image. If not, run the image automatically

case "$1" in
-s)
exit 0
;;
*)
/usr/bin/docker-compose -f docker-compose.yml up -d
;;
esac

echo "Dell Inc. DNE PAQX docker image loaded successfully."

exit $RETVAL
