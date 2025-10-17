BEGIN
  DBMS_CLOUD.CREATE_CREDENTIAL(
    credential_name => 'CRED_NAME_YOU_CHOOSE',
    user_ocid       => 'ocid1.user.oc1.....',
    tenancy_ocid    => 'ocid1.tenancy.oc1.....',
    fingerprint     => 'a1:b2:c3:d4:e5:f6:a7:b8:c9:d0:e1:f2:a3:b4:c5:d6',
    private_key     => q'{
-----BEGIN RSA PRIVATE KEY-----
... body of key ...
-----END RSA PRIVATE KEY-----
}'
  );
END;
