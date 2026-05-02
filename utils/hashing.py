from passlib.context import CryptContext

pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")

def hash_password(password:str)->str:
    """one way convention of plaintext into dcrypt hash.Cannot be reversed."""
    return pwd_context.hash(password)
def verify_password(plain:str,hashed:str)->bool:
    """check if the plain password matches the stored bcrypt hash."""
    return pwd_context.verify(plain,hashed)