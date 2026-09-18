"""Generate self-signed HTTPS certificate for local development."""
import os
import datetime
import ipaddress
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

cert_dir = os.path.dirname(os.path.abspath(__file__))

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COMMON_NAME, 'localhost'),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'NEURO_PREDICT_SYS'),
])

cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
    .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365))
    .add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName('localhost'),
            x509.IPAddress(ipaddress.IPv4Address('127.0.0.1')),
        ]),
        critical=False,
    )
    .sign(key, hashes.SHA256())
)

cert_path = os.path.join(cert_dir, 'cert.pem')
key_path = os.path.join(cert_dir, 'key.pem')

with open(cert_path, 'wb') as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))
with open(key_path, 'wb') as f:
    f.write(key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    ))

print(f"Certificate: {cert_path}")
print(f"Private key: {key_path}")
print("Valid for 365 days. Add to browser trust store for local dev.")
