# server certs

- `openssl genpkey -algorithm RSA -out rootCA.key -pkeyopt rsa_keygen_bits:4096` to make the root CA's private key
- `openssl req -x509 -new -nodes -key rootCA.key -sha256 -days 3650 -out rootCA.crt -subj "/C=US/ST=Michigan/L=Ann Arbor/O=Example University/OU=IT/CN=Root CA"` to make the root CA's certificate
  - use `openssl x509 -text -noout -in rootCA.crt | grep -e Issuer -e Subject | grep -v -e Public -e Key` to show that the Issuer and Subject are the same.  This is what you want for a root CA.
- `openssl genpkey -algorithm RSA -out intermediateCA.key -pkeyopt rsa_keygen_bits:4096` to make the intermediate CA's private key
- `openssl req -new -key intermediateCA.key -out intermediateCA.csr -subj "/C=US/ST=Michigan/L=Ann Arbor/O=Example University/OU=IT/CN=Intermediate CA"` to make a CSR for the intermediate CA
- make the first.conf
- `vim first.conf` and paste:
```shell
[ v3_ca ]
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid:always,issuer
basicConstraints = critical, CA:true
keyUsage = critical, digitalSignature, cRLSign, keyCertSign
```
- `openssl x509 -req -in intermediateCA.csr -CA rootCA.crt -CAkey rootCA.key -CAcreateserial -out intermediateCA.crt -days 1825 -sha256 -extfile first.conf -extensions v3_ca` to sign the CSR by the root CA to make a certificate for the intermediate CA
  - use `openssl x509 -text -noout -in intermediateCA.crt | grep -e Issuer -e Subject | grep -v -e Public -e Key` to show that the intermediate CA's cert was issued by the root CA.  I.e. the Issuer is the same as the root CA's Subject.  The CN (Common Name) of the intermediate CA's cert Issuer is the same as the root CA's cert Subject.
- `openssl genpkey -algorithm RSA -out server.key -pkeyopt rsa_keygen_bits:2048` to make a private key for the server
- `openssl req -new -key server.key -out server.csr -subj "/C=US/ST=Michigan/L=Ann Arbor/O=Example University/OU=IT/CN=rdlu0037.ddns.med.umich.edu"` to make a CSR for the server.  You can use simply the hostname for the CN value.
- `vim second.conf` and paste:
```shell
[ v3_end_entity ]
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid,issuer
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
```
- `openssl x509 -req -in server.csr -CA intermediateCA.crt -CAkey intermediateCA.key -CAcreateserial -out server.crt -days 825 -sha256 -extfile second.cnf -extfile <(printf 'subjectAltName=IP:10.17.105.79')` to sign the server's CSR by the intermediate CA to make a certificate for the server
  - I removed `-extensions v3_end_entity` suggested by UMGPT because it threw a syntax error
  - I tried using `-addext subjectAltName=IP:10.17.105.79` in place of `-extfile <(printf 'subjectAltName=IP:10.17.105.79')`, which should work on newer versions of openssl but didn't have luck
  - rather than using `-extfile <(printf 'subjectAltName=IP:10.17.105.79')`, I put `subjectAltName=IP:10.17.105.79` in `second.cfg` but it didn't work
  - use `openssl x509 -text -noout -in server.crt | grep -e Issuer -e Subject -e IP | grep -v -e Public -e Key` to 1) show that the server's Issuer is the same as the intermediate CA's Subject and 2) that we added the IP address as the Subject Alternative Name (SANN)
- `sudo cp rootCA.crt server.crt server.key /mosquitto/certs`
  - These 3 files end up in the .conf file after the options `cafile`, `certfile` and `keyfile`, respectively.

# client certs

- `cat server.crt intermediateCA.crt rootCA.crt > chain.crt`
  - The chain file is used by a client
- `openssl genpkey -algorithm RSA -out client.key -pkeyopt rsa_keygen_bits:2048` to make a private key for the client
- `openssl req -new -key client.key -out client.csr` to make a CSR for the client
  - leave all fields empty
- `openssl x509 -req -in client.csr -CA intermediateCA.crt -CAkey intermediateCA.key -CAcreateserial -out client.crt -days 825 -sha256 -extfile second.conf` to sign the client's CSR by the intermediate CA to make a certificate for the client
  - notice that the IP address isn't being baked into the certificate
  - The `chain.crt`, `client.crt` and `client.key` files will be used by the client.

# client certs with baked in client ID as the common name

- `openssl req -new -key client.key -out client.csr -subj "/C=US/ST=Michigan/L=Ann Arbor/O=Example University/OU=IT/CN=test-client"` to make a CSR for the client
  - When the directive `use_identity_as_username true` is the .conf, you won't need to provide a client ID since it will be obtained from the client's .crt
  - The client cert's CN is used for the username upon making a connection.  The server's CN, which must be coming from the server's cert in the chain is being used for the client ID prefix.


[medium](https://medium.com/two-cents/certificate-chain-example-e37d68c3a3f0#:%7E:text=To%20create%20a%20file%20with%20the%20certificate%20chain,AWS%20Certificate%20manager%3A%20cat%20TrustedSecureCertificateAuthority5.crt%20USERTrustRSAAddTrustCA.crt%20%3E%20Certificate_Chain.crt)

- server = STAR_mydomain.crt
  - `Issuer: C=US, ST=DE, L=Wilmington, O=Corporation Service Company, CN=Trusted Secure Certificate Authority 5
    Subject: my subject`
  - the Issuer is the same as the intermediate CA's Subject
- intermediate = TrustedSecureCertificateAuthority5.crt
  - `Issuer: C=US, ST=New Jersey, L=Jersey City, O=The USERTRUST Network, CN=USERTrust RSA Certification Authority
    Subject: C=US, ST=DE, L=Wilmington, O=Corporation Service Company, CN=Trusted Secure Certificate Authority 5`
  - Issuer is the same as the third CA's Subject
- third = specific to this example
  - `Issuer: C=SE, O=AddTrust AB, OU=AddTrust External TTP Network, CN=AddTrust External CA Root
    Subject: C=US, ST=New Jersey, L=Jersey City, O=The USERTRUST Network, CN=USERTrust RSA Certification Authority`
- root = USERTrustRSAAddTrustCA.crt
  - `Issuer: C=SE, O=AddTrust AB, OU=AddTrust External TTP Network, CN=AddTrust External CA Root
    Subject: C=SE, O=AddTrust AB, OU=AddTrust External TTP Network, CN=AddTrust External CA Root`
  - same Issuer and Subject
  
- *Issuer* of a cert should be the same as the *Subject* of the next one up (to the right in the chain) up to the root CA, which has the same Subject and Issuer
- The CA that issues a cert that you're trusting should be on the system,
- use `openssl x509 -text -noout -in <certificate>` to inspect a cert
  - my `server.crt` has `Issuer: C = AU, ST = Some-State, O = Internet Widgits Pty Ltd` and `Subject: C = AU, ST = Some-State, O = Internet Widgits Pty Ltd` so there's no chain
- his chain is below, which means that he's not including the root CA in the chain, however, he mentions that the root is sometimes added when you're self-signing
```shell
cat STAR_mydomain.crt TrustedSecureCertificateAuthority5.crt USERTrustRSAAddTrustCA.crt > Certificate_Chain.crt
```

