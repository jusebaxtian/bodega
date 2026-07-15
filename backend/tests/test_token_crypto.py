from app.services.token_crypto import decrypt_token, encrypt_token


def test_token_encryption_roundtrip():
    raw = "EAABsomeFakeMetaAccessToken1234567890"
    encrypted = encrypt_token(raw)

    assert encrypted != raw
    assert raw not in encrypted

    assert decrypt_token(encrypted) == raw
