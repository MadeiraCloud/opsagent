Name:           docker
Version:        1.2.0
Release:        1%{?dist}
Summary:        An open source project to pack, ship and run any application as a lightweight container

Group:          Applications/System
License:        Apache-2.0
URL:            http://www.docker.io/
Source0:        https://get.docker.io/builds/Linux/x86_64/docker-%{version}
Source1:        docker.service

Requires:       shadow-utils


# as debug as no build
%define debug_package %{nil}
%define archivedir docker-%{version}
%define realname docker


%description
Docker is an open-source engine that automates the deployment of any application as a lightweight, portable, self-sufficient container that will run virtually anywhere.


%prep
%setup -q -c %{archivedir} -T


%build
# no build


%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/usr/bin
install -m 0755 %{SOURCE0} %{buildroot}/%{_bindir}/%{realname}
mkdir -p %{buildroot}/etc/init.d
install -m 0755 %{SOURCE1} %{buildroot}/%{_sysconfdir}/init.d/%{realname}


%clean
rm -rf %{buildroot}


%files
%defattr(-,root,root,-)
%{_bindir}/docker
%{_sysconfdir}/init.d/docker


%pre
getent group %{realname} >/dev/null || groupadd -r %{realname}


%changelog
* Mon Sep 1 2014 Thibault Bronchain <thibault@visualops.io> - 1.2.0
- Create package
