#  IRIS Source Code
#  Copyright (C) 2021 - Airbus CyberSecurity (SAS) - https://www.airbus-cyber-security.com
#
#  Licensed under the LGPL v3.0 - the "License";
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      https://www.gnu.org/licenses/lgpl-3.0.html
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import base64
import logging as log

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from flask import current_app


def _derive_integration_key() -> bytes:
    secret = current_app.config['SECRET_KEY']
    if isinstance(secret, str):
        secret = secret.encode()

    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'iris-integration-encryption'
    )
    return base64.urlsafe_b64encode(hkdf.derive(secret))


def encrypt_field(plaintext: str) -> str:
    if not plaintext:
        return plaintext
    try:
        return Fernet(_derive_integration_key()).encrypt(plaintext.encode()).decode()
    except Exception as e:
        log.error(f'Failed to encrypt integration field: {e}')
        raise


def decrypt_field(ciphertext: str) -> str:
    if not ciphertext:
        return ciphertext
    try:
        return Fernet(_derive_integration_key()).decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        log.error('Failed to decrypt integration field - key mismatch or data corrupted')
        raise
    except Exception as e:
        log.error(f'Failed to decrypt integration field: {e}')
        raise