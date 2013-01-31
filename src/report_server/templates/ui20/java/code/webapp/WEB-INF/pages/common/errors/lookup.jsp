<%@ taglib uri="http://rhn.redhat.com/rhn" prefix="rhn" %>
<%@ taglib uri="http://struts.apache.org/tags-bean" prefix="bean" %>
<html:xhtml/>
<html>
<body>

<rhn:require acl="user_authenticated()">

<h1>
  <img src="/img/rhn-icon-warning.gif"
       alt="<bean:message key='error.common.errorAlt' />" />
  ${error.localizedTitle}
</h1>

<p><bean:message key="lookup.jsp.summary"/></p>
    <ol>
      <li>${error.localizedReason1}</li>
      <li>${error.localizedReason2}</li>
      <li><bean:message key="lookup.jsp.reason3"/></li>
    </ol>

</rhn:require>

</body>
</html>
