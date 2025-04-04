This code can be used to send email notifications when new Cisco bugs appear that meet specific conditions. It uses the support API https://developer.cisco.com/site/support-apis/ which requires either SNTC or PSS.
Note: Notification is not coded in yet, new bugs are logged under main.log

To start using:

Set the following venv variables:

API_KEY=
API_SECRET=

Then enter the platforms to monitor in platform.cfg using the following format:

Platform, Software Version, Minimum Severity, Minimum Case Count
For example: Cisco Catalyst 9300 Series Switches, 17.6.5, 2, 3

Repeated runs will check if any new bugs have appeared since the last run.
