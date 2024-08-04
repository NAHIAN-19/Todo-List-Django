import secrets
from cryptography.fernet import Fernet

def generate_secret_key():
    return ''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50))

def generate_fernet_key():
    return Fernet.generate_key().decode()

if __name__ == "__main__":
    secret_key = generate_secret_key()
    fernet_key = generate_fernet_key()
    
    env_content = f"""
SECRET_KEY={secret_key}
FERNET_KEY={fernet_key}

# Email settings
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password
# to get EMAIL_HOST_PASSWORD follow this link : https://www.geeksforgeeks.org/setup-sending-email-in-django-project/
"""
    
    with open(".env", "w") as env_file:
        env_file.write(env_content)
    
    print("The .env file has been created with the generated keys and email configuration.")
