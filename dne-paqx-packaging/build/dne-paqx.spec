#
# Copyright (c) 2017 Dell Inc. or its subsidiaries.  All Rights Reserved.
# Dell EMC Confidential/Proprietary Information
#
Summary: Dell Inc. DNE PAQX
Name: cpsd-dne-paqx-services
Version: %_version
Release: %_revision
License: Commercial
Vendor: Dell Inc.
Group: System Environment/Dell Inc. Applications
URL: http://www.dell.com
Requires: rcm-fitness-common

%define _use_internal_dependency_generator 0
%define __find_requires %{nil}

%description
Dell Inc. DNE PAQX


##############################################################################
# build
##############################################################################
%build

# Creates directory if it doesn't exist
# $1: Directory path
init_dir ()
{
    [ -d $1 ] || mkdir -p $1
}

##############################################################################
# check and create the common directories
##############################################################################
init_dir ${RPM_BUILD_ROOT}/usr/lib/systemd/system


##############################################################################
# check and create the root directory
##############################################################################
init_dir ${RPM_BUILD_ROOT}/opt/dell
init_dir ${RPM_BUILD_ROOT}/opt/dell/cpsd
init_dir ${RPM_BUILD_ROOT}/opt/dell/cpsd/dne-paqx


##############################################################################
# check and create the directories for the service
##############################################################################

SERVICE_BUILD_ROOT=${RPM_BUILD_ROOT}/opt/dell/cpsd/dne-paqx

init_dir ${SERVICE_BUILD_ROOT}
init_dir ${SERVICE_BUILD_ROOT}/install
init_dir ${SERVICE_BUILD_ROOT}/install/dell-dne-paqx-web
init_dir ${SERVICE_BUILD_ROOT}/install/dell-dne-paqx-ess
init_dir ${SERVICE_BUILD_ROOT}/image
init_dir ${SERVICE_BUILD_ROOT}/image/dne-paqx-web
init_dir ${SERVICE_BUILD_ROOT}/image/engineering-standards-service


##############################################################################
# copy the image to the required directory
##############################################################################
cp -r ${RPM_SOURCE_DIR}/target/dependency/dne-paqx/* ${SERVICE_BUILD_ROOT}/image/dne-paqx-web
cp -r ${RPM_SOURCE_DIR}/target/dependency/engineering-standards-service/* ${SERVICE_BUILD_ROOT}/image/engineering-standards-service


##############################################################################
# copy the scripts to the install directory
##############################################################################
cp -rf ${RPM_SOURCE_DIR}/build/install.sh ${SERVICE_BUILD_ROOT}/install
cp -rf ${RPM_SOURCE_DIR}/build/remove.sh ${SERVICE_BUILD_ROOT}/install
cp -rf ${RPM_SOURCE_DIR}/build/upgrade.sh ${SERVICE_BUILD_ROOT}/install


##############################################################################
# copy the unit file
##############################################################################
cp ${RPM_SOURCE_DIR}/build/dell-dne-paqx.service ${RPM_BUILD_ROOT}/usr/lib/systemd/system
cp ${RPM_SOURCE_DIR}/build/dell-dne-paqx-web.service ${RPM_BUILD_ROOT}/usr/lib/systemd/system
cp ${RPM_SOURCE_DIR}/build/dell-dne-paqx-ess.service ${RPM_BUILD_ROOT}/usr/lib/systemd/system

cp -r ${RPM_SOURCE_DIR}/target/dependency/dne-paqx/docker-compose.yml ${SERVICE_BUILD_ROOT}/install/dell-dne-paqx-web/docker-compose.yml
cp -r ${RPM_SOURCE_DIR}/target/dependency/engineering-standards-service/docker-compose.yml ${SERVICE_BUILD_ROOT}/install/dell-dne-paqx-ess/docker-compose.yml

##############################################################################
# pre
##############################################################################
%pre
getent group dell >/dev/null || /usr/sbin/groupadd -f -r dell
getent passwd dnepx >/dev/null || /usr/sbin/useradd -r -g dell -s /sbin/nologin -M dnepx
exit 0


##############################################################################
# post
##############################################################################
%post
if [ $1 -eq 1 ];then
    /bin/sh /opt/dell/cpsd/dne-paqx/install/install.sh
elif [ $1 -eq 2 ];then
    /bin/sh /opt/dell/cpsd/dne-paqx/install/upgrade.sh
else
    echo "Unexpected argument passed to RPM %post script: [$1]"
    exit 1
fi
exit 0


##############################################################################
# preun
##############################################################################
%preun
if [ $1 -eq 0 ];then
    /bin/sh /opt/dell/cpsd/dne-paqx/install/remove.sh
fi
exit 0

##############################################################################
# configure directory and file permissions
##############################################################################
%files

%attr(644,root,root) /usr/lib/systemd/system/dell-dne-paqx.service
%attr(644,root,root) /usr/lib/systemd/system/dell-dne-paqx-web.service
%attr(644,root,root) /usr/lib/systemd/system/dell-dne-paqx-ess.service

%attr(0754,dnepx,dell) /opt/dell/cpsd/dne-paqx
%attr(0755,dnepx,dell) /opt/dell/cpsd/dne-paqx/install
%attr(0755,dnepx,dell) /opt/dell/cpsd/dne-paqx/install/dell-dne-paqx-web
%attr(0755,dnepx,dell) /opt/dell/cpsd/dne-paqx/install/dell-dne-paqx-ess
%attr(0755,dnepx,dell) /opt/dell/cpsd/dne-paqx/image
%attr(0755,dnepx,dell) /opt/dell/cpsd/dne-paqx/image/dne-paqx-web
%attr(0755,dnepx,dell) /opt/dell/cpsd/dne-paqx/image/engineering-standards-service
