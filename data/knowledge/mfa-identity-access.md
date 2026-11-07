# MFA and Identity Access

Northstar uses Okta for single sign-on and multi-factor authentication.

Troubleshooting steps:
1. Confirm the device date and time are set automatically.
2. Retry the push challenge and verify the request location before approving.
3. If push notifications fail, use a backup verification method already enrolled in Okta.
4. If the employee replaced their phone, create an identity access ticket after confirmation.
5. If there are unexpected MFA prompts, stop and report the event as a potential account compromise.

IT support will never ask for passwords, MFA codes, or recovery codes in chat.
