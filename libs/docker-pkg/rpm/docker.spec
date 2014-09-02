Name:           docker
Version:        1.2.0
Release:        1
Summary:        An open source project to pack, ship and run any application as a lightweight container

Group:          Applications/System
License:        Apache-2.0
URL:            http://www.docker.io/
Source:         %{name}-%{version}.tar.gz

Requires:       shadow-utils

BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root

# no debug as no build
%define         __spec_install_post %{nil}
%define         debug_package %{nil}
%define         __os_install_post %{_dbpath}/brp-compress
%define         archivedir docker-%{version}
%define         realname docker


%description
Docker is an open-source engine that automates the deployment of any application as a lightweight, portable, self-sufficient container that will run virtually anywhere.


%prep
%setup -q


%build
# no build


%install
rm -rf %{buildroot}
mkdir -p  %{buildroot}
# in builddir
cp -a * %{buildroot}


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
