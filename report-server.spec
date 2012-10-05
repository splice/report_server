# report-server package -------------------------------------------------------
Name:		report-server
Version:	0.2
Release:	1%{?dist}
Summary:	Reporting server for reporting RHIC net aggregate usage.

Group:		Development/Languages
License:	GPLv2+
URL:		https://github.com/splice/report_server
Source0:	%{name}-%{version}.tar.gz

BuildRequires:	python-setuptools
BuildRequires:  python2-devel


%description
Reporting server for reporting RHIC net aggregate usage.


# report-server import package ------------------------------------------------
%package import
Summary:    Reporting server import application
Group:		Development/Languages


%description import
Reporting server import application


%prep
%setup -q


%build
pushd src
%{__python} setup.py build
popd


%install
rm -rf %{buildroot}

# Install source
pushd src
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
popd

# Install template files
mkdir -p %{buildroot}/%{_usr}/lib/report_server/report_import
cp -R src/report_server/templates %{buildroot}/%{_usr}/lib/report_server
cp -R src/report_server/report_import/templates %{buildroot}/%{_usr}/lib/report_server/report_import

# Install static files
mkdir -p %{buildroot}/%{_localstatedir}/www/html/report_server/sreport
cp -R src/report_server/sreport/static %{buildroot}/%{_localstatedir}/www/html/report_server/sreport

# Remove egg info
rm -rf %{buildroot}/%{python_sitelib}/*.egg-info


%files 
%defattr(-,root,root,-)
%{python_sitelib}/report_server
%defattr(-,apache,apache,-)
%{_usr}/lib/report_server
%{_localstatedir}/www/html/report_server
 

%files import
%defattr(-,root,root,-)
%{python_sitelib}/report_server/report_import
%defattr(-,apache,apache,-)
%{_usr}/lib/report_server/report_import


%clean
rm -rf %{buildroot}


%changelog
* Fri Oct 05 2012 James Slagle <jslagle@redhat.com> 0.2-1
- new package built with tito

