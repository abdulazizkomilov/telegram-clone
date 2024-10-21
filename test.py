from twilio.rest import Client

account_sid = 'AC8ac82a9fc75be9aaf84ab705ba8a3c13'
auth_token = 'de4bd40a020e6c4add2a0910c546594d'
service_sid = 'VAd2e8ae742a12ab28453d0ae8b0e32d89'

client = Client(account_sid, auth_token)

try:
    verification = client.verify.v2.services(service_sid).verifications.create(
        to='+998931159963',
        channel='sms'
    )
    print(f"Verification SID: {verification.sid}")

except Exception as e:
    print(f"Error: {e}")
