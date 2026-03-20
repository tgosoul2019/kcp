# RFC-001: KCP Core Protocol Specification

**Status:** Draft / Active Research
**Métodos Principais:**
1. `KCP_SIGN`: Gera o DNA do dado usando SHA-512 e Ed25519.
2. `KCP_FREEZE`: Serializa o conhecimento para "Super Personagens" (S3/Local Storage) com criptografia de envelope.
3. `KCP_THAW`: Recupera e valida a linhagem de um bloco frio.

**Conectividade:**
* Suporte nativo ao **MCP (Model Context Protocol)** para integração direta com LLMs (Claude, GPT, Gemini).
* Interface gRPC para Sidecars de alta performance.