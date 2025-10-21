import bcrypt


def _prepare_password(password: str) -> bytes:
    """
    Prepare password for bcrypt by encoding and truncating to 72 bytes.

    Bcrypt has a maximum password length of 72 bytes. This function
    ensures passwords are properly encoded and truncated to this limit.

    Args:
        password: The plaintext password

    Returns:
        Password as bytes, truncated to 72 bytes if necessary
    """
    password_bytes = password.encode('utf-8')
    # Bcrypt has a 72-byte limit
    if len(password_bytes) > 72:
        return password_bytes[:72]
    return password_bytes


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plaintext password against its hash.

    Args:
        plain: The plaintext password to verify
        hashed: The bcrypt hash to verify against

    Returns:
        True if password matches, False otherwise
    """
    password_bytes = _prepare_password(plain)
    hashed_bytes = hashed.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def get_password_hash(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.

    Args:
        password: The plaintext password to hash

    Returns:
        Bcrypt hash of the password as a string
    """
    password_bytes = _prepare_password(password)
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')
