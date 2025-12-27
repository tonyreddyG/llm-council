# Scripts

Utility scripts for the LLM Council project.

## generate_certs.py

Generates self-signed SSL certificates for local HTTPS development.

**Usage:**
```bash
python scripts/generate_certs.py
```

This will create `certs/cert.pem` and `certs/key.pem` files for HTTPS support.

**Note:** These are self-signed certificates for development only. Browsers will show a security warning that you'll need to accept.
