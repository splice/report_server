#SELinux
%global selinux_policyver %(%{__sed} -e 's,.*selinux-policy-\\([^/]*\\)/.*,\\1,' /usr/share/selinux/devel/policyhelp || echo 0.0.0)

# report-server package -------------------------------------------------------
Name:		report-server
Version:	0.81
Release:	1%{?dist}
Summary:	Reporting server for Splice.

Group:		Development/Languages
License:	GPLv2+
URL:		https://github.com/splice/report_server
Source0:	%{name}-%{version}.tar.gz

BuildRequires:  python-setuptools
BuildRequires:  python2-devel

Requires:   mongodb-server
Requires:   pymongo
Requires:   httpd
Requires:   mod_wsgi
Requires:   mod_ssl
Requires:   python-isodate
Requires:   Django
Requires:   python-django-tastypie
Requires:   python-django-tastypie-mongoengine
Requires:   python-mongoengine
Requires:   python-mongodbforms
Requires:   python-passlib
Requires:   pymongo-gridfs
Requires:   %{name}-common = %{version}-%{release}
Requires:   %{name}-import = %{version}-%{release}
Requires:   %{name}-selinux = %{version}-%{release}
Requires:   splice-common


%description
Reporting server for Splice.


# report-server import package ------------------------------------------------
%package import
Summary:    Reporting server import application
Group:		Development/Languages

Requires:   mongodb-server
Requires:   pymongo
Requires:   httpd
Requires:   mod_wsgi
Requires:   mod_ssl
Requires:   python-bson
Requires:   python-isodate
Requires:   Django
Requires:   python-django-tastypie
Requires:   python-django-tastypie-mongoengine
Requires:   python-mongoengine
Requires:   %{name}-common = %{version}-%{release}
Requires:   pymongo-gridfs
Requires:   splice-common
Requires:   rhic-serve-rest
Requires:   rhic-serve-rcs
Requires:   rhic-serve-common


%description import
Reporting server import application

# report-server oracle package ------------------------------------------------
%package rs-oracle
Summary:    libraries required for an Oracle database
Group:		Development/Languages

Requires:   cx_Oracle

%description rs-oracle
Reporting server Oracle libraries

# report-server postgresql package ------------------------------------------------
%package rs-postgresql
Summary:    libraries required for a Postgresql database
Group:		Development/Languages

Requires:   python-psycopg2

%description rs-postgresql
Reporting server postgresql libraries


%package common
Summary:    Common libraries for report-server.
Group:      Development/Languages

%description common
Common libraries for report-server.

%package        selinux
Summary:        Splice Report Server SELinux policy
Group:          Development/Languages
BuildRequires:  rpm-python
BuildRequires:  make
BuildRequires:  checkpolicy
BuildRequires:  selinux-policy-devel
# el6, selinux-policy-doc is the required RPM which will bring below 'policyhelp'
BuildRequires:  /usr/share/selinux/devel/policyhelp
BuildRequires:  hardlink
Requires: selinux-policy >= %{selinux_policyver}
Requires(post): policycoreutils-python 
Requires(post): selinux-policy-targeted
Requires(post): /usr/sbin/semodule, /sbin/fixfiles, /usr/sbin/semanage
Requires(postun): /usr/sbin/semodule

%description  selinux
SELinux policy for Splice Report Server

%package doc
Summary:    Splice Report Server documentation
Group:      Development/Languages

BuildRequires:  python-sphinx
BuildRequires:  python-sphinxcontrib-httpdomain

%description doc
Splice Report Server documentation


%prep
%setup -q


%build
pushd src
%{__python} setup.py build
popd
# SELinux Configuration
cd selinux
perl -i -pe 'BEGIN { $VER = join ".", grep /^\d+$/, split /\./, "%{version}.%{release}"; } s!0.0.0!$VER!g;' report-server.te
./build.sh
cd -
# Sphinx documentation
pushd doc
make html
popd


%install
rm -rf %{buildroot}
pushd src
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
popd
mkdir -p %{buildroot}/%{_sysconfdir}/splice/conf.d/
mkdir -p %{buildroot}/%{_sysconfdir}/httpd/conf.d/
mkdir -p %{buildroot}/%{_var}/log/%{name}
mkdir -p %{buildroot}/%{_usr}/lib/report_server
mkdir -p %{buildroot}/%{_localstatedir}/www/html/report_server/
mkdir -p %{buildroot}/%{_sysconfdir}/rc.d/init.d


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

# Install WSGI script & httpd conf
cp -R srv %{buildroot}
cp etc/httpd/conf.d/%{name}.conf %{buildroot}/%{_sysconfdir}/httpd/conf.d/
cp -R etc/splice/report.conf %{buildroot}/%{_sysconfdir}/splice/conf.d/
cp -R etc/rc.d/init.d %{buildroot}/%{_sysconfdir}/rc.d

# Remove egg info
rm -rf %{buildroot}/%{python_sitelib}/*.egg-info

# Install SELinux policy modules
cd selinux
./install.sh %{buildroot}%{_datadir}
mkdir -p %{buildroot}%{_datadir}/%{name}/selinux
cp enable.sh %{buildroot}%{_datadir}/%{name}/selinux
cp uninstall.sh %{buildroot}%{_datadir}/%{name}/selinux
cp relabel.sh %{buildroot}%{_datadir}/%{name}/selinux
cd -

# Documentation
mkdir -p %{buildroot}/%{_docdir}/%{name}
cp LICENSE %{buildroot}/%{_docdir}/%{name}
cp -R doc/_build/html %{buildroot}/%{_docdir}/%{name}


%post selinux
# Enable SELinux policy modules
if /usr/sbin/selinuxenabled ; then
 %{_datadir}/%{name}/selinux/enable.sh %{_datadir}
fi

# Continuing with using posttrans, as we did this for Pulp and it worked for us.
# restorcecon wasn't reading new file contexts we added when running under 'post' so moved to 'posttrans'
# Spacewalk saw same issue and filed BZ here: https://bugzilla.redhat.com/show_bug.cgi?id=505066
%posttrans selinux
if /usr/sbin/selinuxenabled ; then
 %{_datadir}/%{name}/selinux/relabel.sh %{_datadir}
fi

%preun selinux
# Clean up after package removal
if [ $1 -eq 0 ]; then
  %{_datadir}/%{name}/selinux/uninstall.sh
  %{_datadir}/%{name}/selinux/relabel.sh
fi
exit 0


%files 
%defattr(-,root,root,-)
%{python_sitelib}/report_server
%defattr(-,apache,apache,-)
%{_usr}/lib/report_server
%{_localstatedir}/www/html/report_server
%dir /srv/%{name}
%dir /var/log/%{name}
/srv/%{name}/webservices.wsgi
%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}.conf
 

%files common
%defattr(-,root,root,-)
%{python_sitelib}/report_server/common
%{python_sitelib}/report_server/__init__.py*
%config(noreplace) %{_sysconfdir}/rc.d/init.d/report-server
%config(noreplace) %{_sysconfdir}/splice/conf.d/report.conf

%files import
%defattr(-,root,root,-)
%{python_sitelib}/report_server/report_import
%defattr(-,apache,apache,-)
%{_usr}/lib/report_server/report_import

%files selinux
%defattr(-,root,root,-)
%doc selinux/%{name}.fc selinux/%{name}.if selinux/%{name}.te
%{_datadir}/%{name}/selinux/*
%{_datadir}/selinux/*/%{name}.pp
%{_datadir}/selinux/devel/include/apps/%{name}.if

%files doc
%doc %{_docdir}/%{name}


%clean
rm -rf %{buildroot}



%changelog
* Wed Apr 17 2013 Wes Hayutin <whayutin@redhat.com> 0.81-1
- have default red hat report added in javascript (whayutin@redhat.com)

* Wed Apr 17 2013 Wes Hayutin <whayutin@redhat.com> 0.80-1
- broke out filter javascript to its own file (whayutin@redhat.com)
- organized spacewalk js files (whayutin@redhat.com)

* Tue Apr 16 2013 wes hayutin <whayutin@redhat.com> 0.79-1
- filter edit now working w/ PUT call to tastypie (whayutin@redhat.com)
- Merge branch 'filters' (whayutin@redhat.com)
- added filter edit, and fixed delete (whayutin@redhat.com)
- unused calls in urls.py (whayutin@redhat.com)
- patch for backbone.js to add a trailing / on DELETE (whayutin@redhat.com)
- Adding sample data from sst (jwmatthews@gmail.com)
- initial filter edit is working (whayutin@redhat.com)
- Work around for flot issue of: Uncaught TypeError: Cannot call method
  'shutdown' of undefined Issue is that flot was attempting to perform some
  'cleanup' code when it detected it's own canvas element was available and
  being reused. Flot had an issue with the reuse code, so we are manually
  removing the "placeholder" element that house the flot canvas
  (jwmatthews@gmail.com)
- Moved some api docs to splice-server sphix documentation
  (jwmatthews@gmail.com)
- added the logout button back in so John can take a look (whayutin@redhat.com)
- updated example json (whayutin@redhat.com)

* Mon Apr 15 2013 Wes Hayutin <whayutin@redhat.com> 0.78-1
- filter api was getting hit before the user was logged in, prompting a
  tastypie login.. fix (whayutin@redhat.com)
- fixed css for dashboard, added filter for report (whayutin@redhat.com)
- fix report margins (whayutin@redhat.com)
- added css style to create filter and filter search (whayutin@redhat.com)
- added client side search for filter list (whayutin@redhat.com)
- sort and pagination working again (whayutin@redhat.com)
- had to loop through models to change null key to id, now deleting one row
  works (whayutin@redhat.com)
- filter add, delete are working, however all filters are deleted
  (whayutin@redhat.com)
- filter templates are working and saved to the model, new interface for
  filters (whayutin@redhat.com)
- work on initial filter setup (whayutin@redhat.com)
- remove img files in default static dir (whayutin@redhat.com)
- added first template (whayutin@redhat.com)
- css clean up (whayutin@redhat.com)

* Thu Apr 11 2013 Wes Hayutin <whayutin@redhat.com> 0.77-1
- update url in space_report (whayutin@redhat.com)
- Update for SpliceServer API unit test (jwmatthews@gmail.com)

* Thu Apr 11 2013 John Matthews <jwmatthews@gmail.com> 0.76-1
- Updated curl scripts to not use cacert when uploading data to
  splice.common.apis (jwmatthews@gmail.com)
- Update SpliceServer API to handle duplicate uploads (jwmatthews@gmail.com)
- clean up of dev and playpen (whayutin@redhat.com)
- clean up of dev and playpen (whayutin@redhat.com)
- have data load script ready for mpu (whayutin@redhat.com)
- updated push scripts, added response to filter post (whayutin@redhat.com)
- couple more changes for test resources and urls (whayutin@redhat.com)
- fix api_report url (whayutin@redhat.com)
- rolled back and fixed several broken items.. (whayutin@redhat.com)
- tests now pass when using run_tests.sh, use production url, moved css in
  index.html to report.css (whayutin@redhat.com)

* Tue Apr 09 2013 John Matthews <jwmatthews@gmail.com> 0.75-1
- Import FilterResource (jwmatthews@gmail.com)

* Tue Apr 09 2013 John Matthews <jwmatthews@gmail.com> 0.74-1
- fix url in test_post_duplicate (whayutin@redhat.com)
- fix api tests for new url (whayutin@redhat.com)
- filter clean up (whayutin@redhat.com)
- added multiauth for filter api (session and basic) allows for website and api
  to use the same tastypie resource (whayutin@redhat.com)
- updated filter api (whayutin@redhat.com)
- filter api seems to be working properly now (whayutin@redhat.com)
- merge in urls.py and api.py (whayutin@redhat.com)
- working on filter api (whayutin@redhat.com)
- added rhic-serve deps back into the spec (whayutin@redhat.com)
- Update to run from RPM (jwmatthews@gmail.com)
- Playpen scripts to run against RPM (jwmatthews@gmail.com)

* Mon Apr 08 2013 John Matthews <jwmatthews@gmail.com> 0.73-1
- Hooked up splice.common.apis to urls.py used by RPM install
  (jwmatthews@gmail.com)
- Added unit tests for Product/Rules splice.common.apis (jwmatthews@gmail.com)
- Adding unit test for PoolAPI (jwmatthews@gmail.com)
- First phase of integrating splice.common.apis, working when run with 'python
  manage.py runserver' - Updated 'Meta' class of each Resource API so that the
  objects would be written to the 'db_alias' controlled in sreport.models -
  Introduced 'Dev' versions of the Resources which use the default
  Authentication instead of the X509Authentication, allowing to run from django
  dev environment (jwmatthews@gmail.com)
- Added an unusued 'SECRET_KEY' to quiet logging error from django
  (jwmatthews@gmail.com)
- Sample scripts to push Pools, Products, Rules to splice.common.api in
  ReportServer (jwmatthews@gmail.com)
- adding filter api (whayutin@redhat.com)

* Thu Apr 04 2013 Wes Hayutin <whayutin@redhat.com> 0.72-1
- added ability to save report filters and execute, just an ugly prototype
  (whayutin@redhat.com)
- Update playpen script and sample data for MarketingProductUsage
  (jwmatthews@gmail.com)
- Adding a temp workaround for MarketingProductUsageResource so it can run with
  manage.py and not require a X509 cert (jwmatthews@gmail.com)
- Updated to use MarketingProductUsage from splice.common.api and added unit
  test. - Unit tests for 'sreport' may be run from 'run_tests.sh' - Logging of
  unit tests will now go to /tmp/*.log - Hooked up APIs for Rules, Product,
  Pool to dev instance of urls.py, will need more testing
  (jwmatthews@gmail.com)
- Update .gitignore for sphinx generated doc/_build (jwmatthews@gmail.com)
- Removed sphinx generated _build dir (jwmatthews@gmail.com)
- moved subscription detail to the system detail page and removed associated
  methods (whayutin@redhat.com)
- add sla (whayutin@redhat.com)
- remove json parse from product_info and facts (whayutin@redhat.com)
- removed santize from model (whayutin@redhat.com)
- cleaned up import of facts and product_usage (whayutin@redhat.com)
- adding mock data for screenshots (weshayutin@gmail.com)
- fixed broken unit test, api url changed (whayutin@redhat.com)
- added warning regarding rhn.conf file (whayutin@redhat.com)
- System details webui update for green/red/yellow circle
  (jwmatthews@gmail.com)
- Update 'view report' dashboard to color circle green/red/yellow based on data
  (jwmatthews@gmail.com)
- fixed report api (whayutin@redhat.com)

* Thu Mar 28 2013 Wes Hayutin <whayutin@redhat.com> 0.71-1
- add inactive systems to panel, clean up sub detail (whayutin@redhat.com)

* Thu Mar 28 2013 Wes Hayutin <whayutin@redhat.com> 0.70-1
- added inactive system option (whayutin@redhat.com)

* Wed Mar 27 2013 wes hayutin <whayutin@redhat.com> 0.69-1
- added subscription details page (whayutin@redhat.com)
- mocking out more function (whayutin@redhat.com)
- added dash to details (whayutin@redhat.com)
- updates to details page (weshayutin@gmail.com)
- add checkin time for view report (weshayutin@gmail.com)
- first pass at spacewalk report export (weshayutin@gmail.com)
- refactoring data export to work w/ spacewalk (weshayutin@gmail.com)

* Mon Mar 18 2013 wes hayutin <weshayutin@gmail.com> 0.68-1
- clean up (weshayutin@gmail.com)
- have dashboard working w/ counts and grid hover (weshayutin@gmail.com)
- creating dashboard (weshayutin@gmail.com)
- changed icon (weshayutin@gmail.com)
- fix default report (weshayutin@gmail.com)
- modified instance to show multiple products and pools per instance
  (weshayutin@gmail.com)
- added some details to the instance details page (whayutin@redhat.com)
- default report (whayutin@redhat.com)
- instance details (whayutin@redhat.com)
- instance detail added (whayutin@redhat.com)
- added product and pool to report (whayutin@redhat.com)
- added product and pool to report (whayutin@redhat.com)
- building report from satellite data (whayutin@redhat.com)
- report-form is working (whayutin@redhat.com)
- added date conversion , and fixed init script logging param
  (whayutin@redhat.com)
- first commit for marketing product usage (whayutin@redhat.com)
- updated marketing product doc (whayutin@redhat.com)
- Merge branch 'master' of github.com:splice/report_server
  (whayutin@redhat.com)
- added mkt product example (whayutin@redhat.com)
- added retrieve options and made some comments (whayutin@redhat.com)
- added log statement w/ product (whayutin@redhat.com)
- have updating product from select box working (whayutin@redhat.com)
- override select cell (whayutin@redhat.com)
- add false product entries (whayutin@redhat.com)
- Merge branch 'master' of github.com:splice/report_server
  (whayutin@redhat.com)
- added some code to demo remediation (whayutin@redhat.com)

* Mon Mar 04 2013 Wes Hayutin <whayutin@redhat.com> 0.67-1
- remove rhic-serve dep (whayutin@redhat.com)

* Mon Mar 04 2013 Wes Hayutin <whayutin@redhat.com> 0.66-1
- remove rhic-serv from dependencies (whayutin@redhat.com)

* Mon Mar 04 2013 Wes Hayutin <whayutin@redhat.com> 0.65-1
- Merge branch 'backbone' (whayutin@redhat.com)
- removed bootstrap css (whayutin@redhat.com)
- removed show details (whayutin@redhat.com)
- test (whayutin@redhat.com)
- update js paths (whayutin@redhat.com)
- fixed javascript date listz update (whayutin@redhat.com)
- little clean up of navigation (whayutin@redhat.com)
- navigation working properly (whayutin@redhat.com)
- fixed unit tests (whayutin@redhat.com)
- have full metering workflow working w/ backbone (whayutin@redhat.com)
- have max page working (whayutin@redhat.com)
- progress w/ tables (whayutin@redhat.com)
- experimenting with different tables (whayutin@redhat.com)
- found a better library for javascript tables and backbone
  (whayutin@redhat.com)
- have a table working w/ backbone (whayutin@redhat.com)
- have form posting and returning the appropriate json (whayutin@redhat.com)
- broke out dates (whayutin@redhat.com)
- form is more complete (whayutin@redhat.com)
- contracts are working.. at the most basic level (whayutin@redhat.com)
- staging change in xhr (whayutin@redhat.com)
- rename javascript file for spacewalk (whayutin@redhat.com)
- clean up javascript (whayutin@redhat.com)
- pulling more javascript out (whayutin@redhat.com)
- pulling javascript out (whayutin@redhat.com)
- added doc (whayutin@redhat.com)
- prepping js files (whayutin@redhat.com)

* Wed Feb 20 2013 Wes Hayutin <whayutin@redhat.com> 0.64-1
- fixing spec bug (whayutin@redhat.com)
- copied report.conf to the wrong dir (whayutin@redhat.com)

* Wed Feb 20 2013 Wes Hayutin <whayutin@redhat.com> 0.63-1
- fixed bug in spec (whayutin@redhat.com)

* Wed Feb 20 2013 Wes Hayutin <whayutin@redhat.com> 0.62-1
- little more clean up (whayutin@redhat.com)
- clean up report and utils (whayutin@redhat.com)
- clean up max module (whayutin@redhat.com)
- clean up (whayutin@redhat.com)
- clean up (whayutin@redhat.com)
- woot! fixed tastypie basic auth issue (whayutin@redhat.com)
- fixed issue w/ form processing (whayutin@redhat.com)
- fixed unit test failure (whayutin@redhat.com)
- collapsed repsponse (whayutin@redhat.com)
- cleaning up views (whayutin@redhat.com)
- removed ReportUsageDaily (whayutin@redhat.com)
- added postgres support (whayutin@redhat.com)
- unit tests now will not drop db (whayutin@redhat.com)
- broke out oracle connection into its own module (whayutin@redhat.com)
- moved auth back over to mongo (whayutin@redhat.com)
- closer to working w/ mongo (whayutin@redhat.com)
- removing need for django oracle model (whayutin@redhat.com)
- workaround for config issue (whayutin@redhat.com)
- fixed unit tests: checkin_service db name and splice server names
  (whayutin@redhat.com)
- fixed config, broke out space/meter into the report.conf
  (whayutin@redhat.com)
- remove print (whayutin@redhat.com)
- all unit tests passing on devel workstation with new data
  (whayutin@redhat.com)
- changed db import to know rhic, accounts, splice serves etc.
  (whayutin@redhat.com)
- fixed unit test and setting (whayutin@redhat.com)
- fixed unit test and setting (whayutin@redhat.com)
- fixed bug in defunt test (whayutin@redhat.com)
- fixing up unit tests (whayutin@redhat.com)
- fixing up unit tests (whayutin@redhat.com)
- fixing up unit tests (whayutin@redhat.com)
- merge master into branch (whayutin@redhat.com)
- fixed authenticate issue I introduced on Friday (whayutin@redhat.com)
- enabling both the spacewalk and default metering apps to work side by side
  (whayutin@redhat.com)
- breaking out spacewalk required URL's from the master branch which will be
  called meter hence forth.  Common urls will remain in sreport.views.py
  (whayutin@redhat.com)
- Revert "both cookie and cred auth is looking good" (whayutin@redhat.com)
- reseting branch (whayutin@redhat.com)
- Revert "java dir somehow got in here" (whayutin@redhat.com)
- Revert "Revert "gutted unneeded elements of the webui and view""
  (whayutin@redhat.com)
- Revert "gutted unneeded elements of the webui and view" (whayutin@redhat.com)
- gutted unneeded elements of the webui and view (whayutin@redhat.com)
- java dir somehow got in here (whayutin@redhat.com)
- both cookie and cred auth is looking good (whayutin@redhat.com)
- broke out auth into two engines cookie and credentials (whayutin@redhat.com)
- Revert "authenticating w/ both a cookie and a login does not appear to be
  supportable" (whayutin@redhat.com)
- authenticating w/ both a cookie and a login does not appear to be supportable
  (whayutin@redhat.com)
- adding login form back in (whayutin@redhat.com)
- Revert "trying out login/logout w/ sessions" (whayutin@redhat.com)
- trying out login/logout w/ sessions (whayutin@redhat.com)
- flush session if spacewalk session is no longer active (whayutin@redhat.com)
- auto create django user from spacewalk session (whayutin@redhat.com)
- fixed issue in the backend.py that was causing the user to be Anonymous
  instead of the oracle user (whayutin@redhat.com)
- still testing (whayutin@redhat.com)
- changed up the view a bit (whayutin@redhat.com)
- I think I have the custom session working atm...  w/ auth_user_backendq\x04U6
  report_server.auth.spacewalk.backends.SpacewalkBackendU\r_auth_user_idq\x05K\
  x02u. (whayutin@redhat.com)
- still testing (whayutin@redhat.com)
- testing (whayutin@redhat.com)
- logging in but ssl mismatch on requests (whayutin@redhat.com)
- login w/ cookie is pretty much working (whayutin@redhat.com)
- adding code to read spacewalk cookies (whayutin@redhat.com)
- created a custom authentication backend for spacewalk (whayutin@redhat.com)
- ok.. had to turn some of the features off like contracts etc.. but logging
  into the report server using a spacewalk oracle backend is working
  (whayutin@redhat.com)
- have django logins working while pointing to the spacewalk oracle db
  (whayutin@redhat.com)
- moving auth to oracle (whayutin@redhat.com)

* Fri Feb 01 2013 John Matthews <jwmatthews@gmail.com> 0.61-1
- Don't throw a 409 on duplicate ReportData objects, log the issue and
  continue. (jwmatthews@gmail.com)

* Fri Feb 01 2013 John Matthews <jwmatthews@gmail.com> 0.60-1
- Fix to ensure 'date' of ProductUsage is always converted to datetime instance
  prior to import_hook being called (jwmatthews@gmail.com)

* Thu Jan 31 2013 John Matthews <jwmatthews@gmail.com> 0.59-1
- Adding debug info to track down issue with SpliceServer upload
  (jwmatthews@gmail.com)

* Thu Jan 31 2013 John Matthews <jwmatthews@gmail.com> 0.58-1
- Fix so SpliceServer API uses same db_alias for looking up if a SpliceServer
  object exists (jwmatthews@gmail.com)

* Thu Jan 31 2013 John Matthews <jwmatthews@gmail.com> 0.57-1
- Fix so SpliceServer data sent through API will be written to the db_alias
  defined in ReportServer's SpliceServer model (jwmatthews@gmail.com)

* Thu Jan 31 2013 John Matthews <jwmatthews@gmail.com> 0.56-1
- Add timezone aware for 'default' (jwmatthews@gmail.com)

* Wed Jan 30 2013 John Matthews <jmatthews@redhat.com> 0.55-1
- Adding upload if 'SpliceServer' API (jmatthews@redhat.com)

* Fri Jan 25 2013 John Matthews <jmatthews@redhat.com> 0.54-1
- Fix for non-gzipped import of ProductUsage data (jmatthews@redhat.com)

* Wed Jan 23 2013 John Matthews <jmatthews@redhat.com> 0.53-1
- Added support for gzip compression for body of request in ProductUsage import
  (jmatthews@redhat.com)
- blanking out config (whayutin@redhat.com)
- Fix ISE on upload of ProductUsage data with an empty body
  (jmatthews@redhat.com)

* Wed Jan 16 2013 wes hayutin <whayutin@redhat.com> 0.52-1
- fixed some issues w/ biz rule report (whayutin@redhat.com)

* Wed Jan 16 2013 wes hayutin <whayutin@redhat.com> 0.51-1
- Merge branch 'master' of github.com:splice/report_server
  (whayutin@redhat.com)
- fixed logging for dev setup (whayutin@redhat.com)
- data sanitize for imports (whayutin@redhat.com)
- fixed terrible date hack (whayutin@redhat.com)

* Mon Jan 14 2013 Wes Hayutin <whayutin@redhat.com> 0.50-1
- changed verbage around rhic/biz rule reports (whayutin@redhat.com)
- made default report a dynamic three months (whayutin@redhat.com)
- fix extra show details bug and csv export issue (whayutin@redhat.com)
- work around for User objects in stakeholder env (whayutin@redhat.com)
- clean up (whayutin@redhat.com)
- report_server perf testing scripts (whayutin@redhat.com)
- first pass at perf tests (whayutin@redhat.com)

* Wed Jan 09 2013 Wes Hayutin <whayutin@redhat.com> 0.49-1
- fixed bug in javascript w/ show/hide button (whayutin@redhat.com)

* Wed Jan 09 2013 Wes Hayutin <whayutin@redhat.com> 0.48-1
- Merge branch 'master' of github.com:splice/report_server
  (whayutin@redhat.com)
- simple report, hide/show details (whayutin@redhat.com)

* Tue Jan 08 2013 John Matthews <jmatthews@redhat.com> 0.47-1
- Removed "mkdir /var/log/report-server" line from spec (jmatthews@redhat.com)
- added a default minimalistic report for satellite (whayutin@redhat.com)
- added authentication to ReportResource deleted redundant code
  (dgao@redhat.com)
- broke out data load tool.. slightly (whayutin@redhat.com)
- broke out a data loading tool from unit tests (whayutin@redhat.com)

* Wed Jan 02 2013 Wes Hayutin <whayutin@redhat.com> 0.46-1
- try to fix selinux issue (whayutin@redhat.com)

* Wed Jan 02 2013 Wes Hayutin <whayutin@redhat.com> 0.45-1
-added rhic-rcs rpm dep
- 

* Wed Jan 02 2013 Wes Hayutin <whayutin@redhat.com> 0.44-1
- changed rhic deps to only rhic-serve-rest (whayutin@redhat.com)
- fixed some new years bugs (whayutin@redhat.com)
- modified wsgi param for django settings (whayutin@redhat.com)

* Wed Dec 12 2012 wes hayutin <whayutin@redhat.com> 0.43-1
- Automatic commit of package [report-server] release [0.42-1].
  (whayutin@redhat.com)
- Moved "SpliceServerResource" back into splice server code base
  (jmatthews@redhat.com)
- Add API for Splice Server metadata (jmatthews@redhat.com)

* Wed Dec 12 2012 wes hayutin <whayutin@redhat.com> 0.42-1
- horrible hack for report api test (whayutin@redhat.com)
- updated report form to cascade changes from contract, fixed dec date bug, and
  some clean up (whayutin@redhat.com)
- added mdu/mcu tests (whayutin@redhat.com)
- adding more api tests (whayutin@redhat.com)
- refactor / clean up (whayutin@redhat.com)
- pep8 clean up (whayutin@redhat.com)
- clean up for pep8 compliance (whayutin@redhat.com)
- minor fix (whayutin@redhat.com)
- fixing unit tests.. failing due to pymongo ObjectId on RHEL6
  (whayutin@redhat.com)
- minor updates to tests (whayutin@redhat.com)
- clean up views and api (whayutin@redhat.com)
- more tests fixes (jslagle@redhat.com)
- test refactorings (jslagle@redhat.com)
- Merge branch 'master' into splice-common (jslagle@redhat.com)
- tests refactorings and fixes (jslagle@redhat.com)
- basic report returned via api (whayutin@redhat.com)
- Merge branch 'master' into splice-common (jslagle@redhat.com)
- Fix broken test (jslagle@redhat.com)
- Fix broken test (jslagle@redhat.com)
- Merge branch 'master' into splice-common (jslagle@redhat.com)
- Remove tests.py now that there is a tests/ (jslagle@redhat.com)
- Merge branch 'master' into splice-common (jslagle@redhat.com)
- able to add some api calls (whayutin@redhat.com)
- adding tests for admin work (whayutin@redhat.com)
- updates (jslagle@redhat.com)
- splice-common refactorings (jslagle@redhat.com)
- Move dev directory under report_server source (jslagle@redhat.com)

* Thu Nov 15 2012 Wes Hayutin
 0.41-1
 <whayutin@redhat.com>
- clean up for admin page (whayutin@redhat.com)
- update rules test (whayutin@redhat.com)
- removed upper limit on gear memory (whayutin@redhat.com)

* Thu Nov 15 2012 Wes Hayutin
 0.40-1
 <whayutin@redhat.com>
- added finite limit to rules (whayutin@redhat.com)
- updated product rules, have fact compliance checking working
  (whayutin@redhat.com)
- first pass at import quarantine ui, also added a ui for system fact non-
  compliance (whayutin@redhat.com)
- api import working against /api/v1/productusage (whayutin@redhat.com)

* Mon Nov 12 2012 Wes Hayutin <whayutin@redhat.com> 0.39-1
* fixed added NAU back in, fixed graph pointer
- 

* Mon Nov 12 2012 Wes Hayutin <whayutin@redhat.com> 0.38-1
- first pass at compliance report (whayutin@redhat.com)
- fixed mdu vs mcu bug, updated js files (whayutin@redhat.com)

* Fri Nov 09 2012 Wes Hayutin
 0.37-1
 <whayutin@redhat.com>
- MCU workflow complete (whayutin@redhat.com)
- changed import to let mongo check for dupes (should increase perf), changed
  workflow for mcu, added ajax spinner (whayutin@redhat.com)
- updated unit tests (whayutin@redhat.com)

* Tue Nov 06 2012 Wes Hayutin <whayutin@redhat.com> 0.36-1
* Demo Server for Sprint 3
- 

* Tue Nov 06 2012 Wes Hayutin <whayutin@redhat.com> 0.35-1
- found bug w/ finding contract data, fixed up the report table css
  (whayutin@redhat.com)
- few minor updates, changed date format, trying to get dates on x-axis
  (whayutin@redhat.com)

* Fri Nov 02 2012 Wes Hayutin
 0.34-1
 <whayutin@redhat.com>
- moved max graph to the top (whayutin@redhat.com)

* Fri Nov 02 2012 Wes Hayutin
 0.33-1
 <whayutin@redhat.com>
- added in contracted use to max (whayutin@redhat.com)
- updated test cases (whayutin@redhat.com)
- updated unit tests (whayutin@redhat.com)

* Fri Nov 02 2012 Wes Hayutin
 0.32-1
 <whayutin@redhat.com>
- have csv export working on firefox and chrome (whayutin@redhat.com)
- ripped out table export and fixed import issue (whayutin@redhat.com)
- added css for report table, removed pdf export (whayutin@redhat.com)

* Thu Nov 01 2012 Wes Hayutin
 0.31-1
 <whayutin@redhat.com>
- fixed contract defaults (whayutin@redhat.com)
- readded tabletools.css and added legend for max graphs (whayutin@redhat.com)
- fix some breakage from failed merge (whayutin@redhat.com)
- yanked javascript out to its own separate file (dgao@redhat.com)
- clicking the row in reports was not working as designed, had to pull it
  (whayutin@redhat.com)
- asdf (whayutin@redhat.com)
- oops accidentally committed some unmerged code (dgao@redhat.com)
- Merge branch 'UI_20' of github.com:splice/report_server into UI_20
  (dgao@redhat.com)
- minor tweak to make instance table updates (dgao@redhat.com)
- taking out tabletools css for the moment (whayutin@redhat.com)
- updated ui for new requirements, firefox is not working atm.. use chrome
  (whayutin@redhat.com)
- clean up (whayutin@redhat.com)
- added ui control test (whayutin@redhat.com)
- fixed unit tests for UI_20 branch (whayutin@redhat.com)
- merge fix (whayutin@redhat.com)
- merge from master (whayutin@redhat.com)
- updated dev setup (whayutin@redhat.com)
- minor change to override min-height from datatable css (dgao@redhat.com)
- clicking report row will now fill both instance_detail and max_data pane
  (dgao@redhat.com)
- converted instance details to datatable removed unnecessary code
  (dgao@redhat.com)
- added click functionality back to detail page to show instance details
  (dgao@redhat.com)
- removed out-dated function/reference (dgao@redhat.com)
- Add sample response (jslagle@redhat.com)
- Now that packaging is done, no need to ever use anything other than
  dev.settings (jslagle@redhat.com)
- initial commit for datatable work (need more cleanup, very messy right now
  and also event handling for checkins (dgao@redhat.com)
- Merge branch 'UI_20' of github.com:splice/report_server into UI_20
  (dgao@redhat.com)
- modified import path for splice models (dgao@redhat.com)

* Fri Oct 26 2012 James Slagle <jslagle@redhat.com> 0.30-1
- Add missing LICENSE file (jslagle@redhat.com)

* Fri Oct 26 2012 James Slagle <jslagle@redhat.com> 0.29-1
- Add some api docs (jslagle@redhat.com)
- Initial docs and packaging (jslagle@redhat.com)

* Fri Oct 26 2012 James Slagle <jslagle@redhat.com> 0.28-1
- Update requires for new rhic-serve packaging (jslagle@redhat.com)

* Thu Oct 25 2012 Wes Hayutin <whayutin@redhat.com> 0.27-1
- django.log does not need to be changed only the parent dir
  (whayutin@redhat.com)

* Thu Oct 25 2012 Wes Hayutin <whayutin@redhat.com> 0.26-1
- fixed bug in spec for report.conf (whayutin@redhat.com)

* Thu Oct 25 2012 Wes Hayutin <whayutin@redhat.com> 0.25-1
- added splice.config and init.d files to spec (whayutin@redhat.com)

* Thu Oct 25 2012 Wes Hayutin <whayutin@redhat.com> 0.24-1
- bug w/ selinux perm for /srv (whayutin@redhat.com)

* Thu Oct 25 2012 Wes Hayutin <whayutin@redhat.com> 0.23-1
- selinux building now (whayutin@redhat.com)

* Thu Oct 25 2012 Wes Hayutin <whayutin@redhat.com> 0.22-1
- add files in spec for selinux (whayutin@redhat.com)

* Thu Oct 25 2012 Wes Hayutin <whayutin@redhat.com> 0.21-1
- Automatic commit of package [report-server] release [0.20-1].
  (whayutin@redhat.com)
- package for report-server-selinux added to spec (whayutin@redhat.com)
- added some more config for selinux, added init.d (whayutin@redhat.com)
- Added some logging for performance measurements to product usage import, also
  now return a CONFLICT if an error occurred during import.  Needs more work to
  return back jsonified list of objects that errored (jmatthews@redhat.com)

* Thu Oct 25 2012 Wes Hayutin <whayutin@redhat.com> 0.20-1
- package for report-server-selinux added to spec (whayutin@redhat.com)
- added some more config for selinux, added init.d (whayutin@redhat.com)

* Thu Oct 25 2012 Wes Hayutin <whayutin@redhat.com> 0.19-1
- missed an url change, added rcs to Requires (whayutin@redhat.com)

* Thu Oct 25 2012 Wes Hayutin <whayutin@redhat.com> 0.18-1
- add gridfs as dep, make a log dir (whayutin@redhat.com)

* Wed Oct 24 2012 Wes Hayutin
 0.17-1
 <whayutin@redhat.com>
- additional changes for packaging (whayutin@redhat.com)
- Automatic commit of package [python-mongodbforms] minor release
  [0.1.4-7.splice]. (whayutin@redhat.com)
- update prep step for proper build root name (whayutin@redhat.com)
- Automatic commit of package [python-mongodbforms] minor release
  [0.1.4-6.splice]. (whayutin@redhat.com)
- update build root (whayutin@redhat.com)
- Automatic commit of package [python-mongodbforms] minor release
  [0.1.4-5.splice]. (whayutin@redhat.com)
- getting a bad exit code from a %%clean (whayutin@redhat.com)
- Automatic commit of package [python-mongodbforms] minor release
  [0.1.4-4.splice]. (whayutin@redhat.com)

* Wed Oct 24 2012 Wes Hayutin
 0.16-1
 <whayutin@redhat.com>
- since mongdbforms requires python-mongoengine.. renaming to python-
  mongodbforms, and making reports require it (whayutin@redhat.com)
- Automatic commit of package [mongodbforms] minor release [0.1.4-3.splice].
  (whayutin@redhat.com)
- seems to be building locally now (whayutin@redhat.com)

* Wed Oct 24 2012 Wes Hayutin
 0.15-1
 <whayutin@redhat.com>
- another attempt to fix mongoddbforms (whayutin@redhat.com)
- trying to fix mongodbform build issue (whayutin@redhat.com)
- updated deps (whayutin@redhat.com)
- Automatic commit of package [mongodbforms] minor release [0.1.4-2.splice].
  (whayutin@redhat.com)
- adding dep source for mongodbforms (whayutin@redhat.com)

* Wed Oct 24 2012 Wes Hayutin
 0.14-1
 <whayutin@redhat.com>
- most of the packaging is complete (whayutin@redhat.com)
- Automatic commit of package [report-server] release [0.13-1].
  (whayutin@redhat.com)

* Wed Oct 24 2012 Wes Hayutin
 0.13-1
 <whayutin@redhat.com>
- fixed imports for packaging (whayutin@redhat.com)

* Tue Oct 23 2012 Wes Hayutin <whayutin@redhat.com> 0.12-1
- changing wsgi name from splice_reports to report-server (whayutin@redhat.com)

* Tue Oct 23 2012 Wes Hayutin <whayutin@redhat.com> 0.11-1
- fix to initial page load, and spec (whayutin@redhat.com)

* Tue Oct 23 2012 Wes Hayutin <whayutin@redhat.com> 0.10-1
- rename srv dir (whayutin@redhat.com)

* Tue Oct 23 2012 Wes Hayutin <whayutin@redhat.com> 0.9-1
- missing files in spec (whayutin@redhat.com)

* Tue Oct 23 2012 Wes Hayutin <whayutin@redhat.com> 0.8-1
- fixed naming for http conf (whayutin@redhat.com)

* Tue Oct 23 2012 Wes Hayutin <whayutin@redhat.com> 0.7-1
- updated packaging (whayutin@redhat.com)
- created a control to prevent imports from stepping on each other
  (whayutin@redhat.com)
- adding rules to production settings.py (whayutin@redhat.com)

* Tue Oct 23 2012 Wes Hayutin <whayutin@redhat.com> 0.6-1
- merge (whayutin@redhat.com)
- fix model change from splice server (whayutin@redhat.com)
- update unit tests (whayutin@redhat.com)
- couple things to clean up (whayutin@redhat.com)
- rename from admin -> ui20 (whayutin@redhat.com)
- added functionality to gray out tab(s) before it can be used moved foo folder
  to admin modified url and view methods to accomodate the move
  (dgao@redhat.com)
- added MongoEncoder and helper methods to jsonify objs (dgao@redhat.com)
- first pass at max daily usage (whayutin@redhat.com)
- updated import for new splice server model (whayutin@redhat.com)
- merge in selinux rules (whayutin@redhat.com)
- added copyright info and graph data (whayutin@redhat.com)
- changed width of graph to occupy 100%% of the existing content space
  (dgao@redhat.com)
- remove debug code (dgao@redhat.com)
- added charting lib for Max Data tab (dgao@redhat.com)
- stubbed out max daily usage (whayutin@redhat.com)
- begin max page (whayutin@redhat.com)
- merge (whayutin@redhat.com)
- minor fixes (whayutin@redhat.com)
- don't reset form after report is generated. added reset button clear out
  report/detail pane if reset button is clicked (dgao@redhat.com)
- added to_dict() to ReportData and ReportDataDaily (dgao@redhat.com)
- fixed import issue (albeit, not very elegant) (dgao@redhat.com)
- fixing import issue (whayutin@redhat.com)
- removed unused files (dgao@redhat.com)
- merge (whayutin@redhat.com)
- had to move foo templates, removed some bad tests, fixed an import in views
  (whayutin@redhat.com)
- intermediate checkin for more fixes from the merge (dgao@redhat.com)
- moved files to the correct location after merge (dgao@redhat.com)
- Merge branch 'master' of git://github.com/segfault923/report_server into
  UI_20 (dgao@redhat.com)
- finished off instance_detail (dgao@redhat.com)
- intermediate changes for instance_detail work initial revision for todo list
  (dgao@redhat.com)
- minor deletion of unused code (dgao@redhat.com)
- added reporting and detail pane (dgao@redhat.com)
- initial revision to centralize everything to one admin page (dgao@redhat.com)

* Fri Oct 19 2012 John Matthews <jmatthews@redhat.com> 0.5-1
- Add requires for 'report-server-common' to 'report-server-import'
  (jmatthews@redhat.com)

* Fri Oct 19 2012 John Matthews <jmatthews@redhat.com> 0.4-1
- Small tweaks to productusage.py after some testing (jmatthews@redhat.com)
- Created a report-server-common RPM, currently it just packages
  report_server/__init__.py this allows report-server-import to function by
  itself (jmatthews@redhat.com)
- Update json parsing to run on el6, might need to revisit for Fedora
  (jmatthews@redhat.com)
- mdu tests need to removed atm (whayutin@redhat.com)
- added max daily usage calulation and unit tests (whayutin@redhat.com)
- broke out unit tests, finished configurable import, added generated to
  instance details page (whayutin@redhat.com)
- removed old count def in products, added tests, refactored how biz rules are
  read in (whayutin@redhat.com)
- fix for hudson path (whayutin@redhat.com)
- finished first pass at custom config (whayutin@redhat.com)
- fix python path for dev settings (whayutin@redhat.com)
- first pass at biz rules as config (whayutin@redhat.com)
- adding custom count (whayutin@redhat.com)
- jboss is <=4 (whayutin@redhat.com)
- change default report settings for splice/report.conf (whayutin@redhat.com)
- missed one import (whayutin@redhat.com)
- missed one import (whayutin@redhat.com)
- fix imports (whayutin@redhat.com)
- reworked batch import, cleaned templates, added logout, cleaned imports
  (whayutin@redhat.com)
- Merge branch 'master' of github.com:splice/report_server
  (whayutin@redhat.com)
- Remove unneeded lines (jslagle@redhat.com)
- Add Requires (jslagle@redhat.com)
- Merge branch 'master' of github.com:splice/report_server
  (whayutin@redhat.com)
- Merge branch 'master' of github.com:splice/report_server merge of updated
  import (whayutin@redhat.com)
- more tests (whayutin@redhat.com)

* Fri Oct 05 2012 James Slagle <jslagle@redhat.com> 0.3-1
- Packaging fixes (jslagle@redhat.com)
- Install all src under a top level report_server directory
  (jslagle@redhat.com)
- Fix file installation path (jslagle@redhat.com)

* Fri Oct 05 2012 James Slagle <jslagle@redhat.com> 0.2-1
- new package built with tito


