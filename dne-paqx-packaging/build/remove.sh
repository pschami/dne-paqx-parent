#!/bin/bash
#
# Copyright (c) 2017 Dell Inc. or its subsidiaries.  All Rights Reserved.
# Dell EMC Confidential/Proprietary Information
#

echo "Removing Dell Inc. DNE PAQX components"

systemctl disable dne-paqx

/bin/sh /opt/dell/cpsd/dne-paqx/image/dne-paqx/remove.sh
/bin/sh /opt/dell/cpsd/dne-paqx/image/engineering-standards-service/remove.sh

echo "Dell Inc. DNE PAQX components removal has completed successfully."

exit 0
