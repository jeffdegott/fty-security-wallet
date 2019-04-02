#
#    fty-security-wallet - Security Wallet to manage JSON document including a public and secret part
#
#    Copyright (C) 2019 Eaton
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

# To build with draft APIs, use "--with drafts" in rpmbuild for local builds or add
#   Macros:
#   %_with_drafts 1
# at the BOTTOM of the OBS prjconf
%bcond_with drafts
%if %{with drafts}
%define DRAFTS yes
%else
%define DRAFTS no
%endif
%define SYSTEMD_UNIT_DIR %(pkg-config --variable=systemdsystemunitdir systemd)
Name:           fty-security-wallet
Version:        1.0.0
Release:        1
Summary:        security wallet to manage json document including a public and secret part
License:        GPL-2.0+
URL:            https://42ity.org
Source0:        %{name}-%{version}.tar.gz
Group:          System/Libraries
# Note: ghostscript is required by graphviz which is required by
#       asciidoc. On Fedora 24 the ghostscript dependencies cannot
#       be resolved automatically. Thus add working dependency here!
BuildRequires:  ghostscript
BuildRequires:  asciidoc
BuildRequires:  automake
BuildRequires:  autoconf
BuildRequires:  libtool
BuildRequires:  pkgconfig
BuildRequires:  systemd-devel
BuildRequires:  systemd
%{?systemd_requires}
BuildRequires:  xmlto
BuildRequires:  gcc-c++
BuildRequires:  libsodium-devel
BuildRequires:  zeromq-devel
BuildRequires:  czmq-devel >= 3.0.2
BuildRequires:  malamute-devel >= 1.0.0
BuildRequires:  openssl-devel
BuildRequires:  log4cplus-devel
BuildRequires:  fty-common-logging-devel
BuildRequires:  fty-common-devel
BuildRequires:  fty-common-mlm-devel
BuildRequires:  cxxtools-devel
BuildRoot:      %{_tmppath}/%{name}-%{version}-build

%description
fty-security-wallet security wallet to manage json document including a public and secret part.

%package -n libfty_security_wallet1
Group:          System/Libraries
Summary:        security wallet to manage json document including a public and secret part shared library

%description -n libfty_security_wallet1
This package contains shared library for fty-security-wallet: security wallet to manage json document including a public and secret part

%post -n libfty_security_wallet1 -p /sbin/ldconfig
%postun -n libfty_security_wallet1 -p /sbin/ldconfig

%files -n libfty_security_wallet1
%defattr(-,root,root)
%{_libdir}/libfty_security_wallet.so.*

%package devel
Summary:        security wallet to manage json document including a public and secret part
Group:          System/Libraries
Requires:       libfty_security_wallet1 = %{version}
Requires:       libsodium-devel
Requires:       zeromq-devel
Requires:       czmq-devel >= 3.0.2
Requires:       malamute-devel >= 1.0.0
Requires:       openssl-devel
Requires:       log4cplus-devel
Requires:       fty-common-logging-devel
Requires:       fty-common-devel
Requires:       fty-common-mlm-devel
Requires:       cxxtools-devel

%description devel
security wallet to manage json document including a public and secret part development tools
This package contains development files for fty-security-wallet: security wallet to manage json document including a public and secret part

%files devel
%defattr(-,root,root)
%{_includedir}/*
%{_libdir}/libfty_security_wallet.so
%{_libdir}/pkgconfig/libfty_security_wallet.pc
%{_mandir}/man3/*
%{_mandir}/man7/*

%prep

%setup -q

%build
sh autogen.sh
%{configure} --enable-drafts=%{DRAFTS} --with-systemd-units
make %{_smp_mflags}

%install
make install DESTDIR=%{buildroot} %{?_smp_mflags}

# remove static libraries
find %{buildroot} -name '*.a' | xargs rm -f
find %{buildroot} -name '*.la' | xargs rm -f

%files
%defattr(-,root,root)
%doc README.md
%{_bindir}/fty-security-wallet
%{_mandir}/man1/fty-security-wallet*
%config(noreplace) %{_sysconfdir}/fty-security-wallet/fty-security-wallet.cfg
%{SYSTEMD_UNIT_DIR}/fty-security-wallet.service
%dir %{_sysconfdir}/fty-security-wallet
%if 0%{?suse_version} > 1315
%post
%systemd_post fty-security-wallet.service
%preun
%systemd_preun fty-security-wallet.service
%postun
%systemd_postun_with_restart fty-security-wallet.service
%endif

%changelog
