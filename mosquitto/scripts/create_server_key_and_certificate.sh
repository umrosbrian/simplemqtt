#!/bin/bash

# ----------------------------------------------------------------------------------------------------------------------
# Create a key for the server then use the signing CA to sign the server's CSR to create a certificate for the server.
# ----------------------------------------------------------------------------------------------------------------------
opts='/C=US/ST=Michigan/L=Ann Arbor/O=University of Michigan/OU=IT/'

# verify that a script was provided as an argument
if [ -z "$1" ] || [ "$1" == '' ]
then
  echo "The IP address of the server needs to provided as an argument."
  exit 1
else
  ip_addr="$1"
fi

cd ../certs
echo "creating private key for the server"
openssl genpkey -algorithm RSA -out server.key -pkeyopt rsa_keygen_bits:2048
echo "creating CSR for the server"
# I haven't figured this out, but Mosquitto will use the server's CN as the client id so I'm providing a CN that \
# reflects a client rather than the server.
openssl req -new -key server.key -out server.csr -subj "${opts}CN=MQTTClient"
echo "using the signing CA to sign the server's CSR to create a certificate for the server"
# the first extfile isn't being used at all.  I wonder if it's needed at all.  Maybe these options are already baked
# into the signing CA's cert.  Yes, they appear to be.  Think of the redirection of printf as appending to the
# server's cert.
openssl x509 -req -in server.csr -CA signingCA.crt -CAkey signingCA.key -CAcreateserial -out server.crt \
-days 825 -sha256 -extfile <(printf "subjectAltName=IP:${ip_addr}")
rm signing_options.conf
printf "\nHere's what it important in the server's certificate.  Everthing but
the CN (Common Name) of Issuer and Subject should be the same.  Also the IP
address of the server has been added as the SANN (Subject Alternative Name).\n\n"
openssl x509 -text -noout -in ../certs/server.crt | grep -e Issuer -e Subject -e IP | grep -v -e Public -e Key
echo


