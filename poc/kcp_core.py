import hashlib
import json
import time
from cryptography.hazmat.primitives.asymmetric import ed25519

class KCPLayer8:
    def __init__(self, identity):
        self.node_id = identity
        self.sk = ed25519.Ed25519PrivateKey.generate()
        self.pk = self.sk.public_key()

    def seal_knowledge(self, text, parent="8d969e..."):
        # Criação do DNA do Conhecimento
        payload = {"data": text, "parent": parent, "ts": time.time()}
        dna = hashlib.sha512(json.dumps(payload).encode()).hexdigest()
        sig = self.sk.sign(dna.encode())
        
        return {
            "header": {"kid": dna, "sig": sig.hex(), "node": self.node_id},
            "body": payload
        }

# Exemplo de uso
kcp = KCPLayer8("Origin-Node-01")
block = kcp.seal_knowledge("YHWH o Alfa e Ômega seja dado toda glória!")
print(json.dumps(block, indent=2))