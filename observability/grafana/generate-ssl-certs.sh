rm -rf data
mkdir data
#    ssl_certificate /ssl/ssl_cert.pem;
#    ssl_certificate_key /ssl/ssl_private_key.key;

openssl req -x509 -newkey rsa:4096 -keyout data/ssl_private_key.pem -out data/ssl_cert.pem -nodes -sha256 -days 365
