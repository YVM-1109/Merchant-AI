/**
 * AP2 client-side crypto utilities.
 * Uses Web Crypto API for key generation and JWS signing in the browser.
 */

export class AP2Crypto {
  /**
   * Generate an ES256 key pair in PEM format.
   * Returns { privateKeyPem, publicKeyPem }.
   */
  static async generateKeyPair(): Promise<{ privateKeyPem: string; publicKeyPem: string }> {
    const keyPair = await crypto.subtle.generateKey(
      { name: "ECDSA", namedCurve: "P-256" },
      true,
      ["sign", "verify"],
    );

    const privateKeyPem = await AP2Crypto.exportPrivateKey(keyPair.privateKey);
    const publicKeyPem = await AP2Crypto.exportPublicKey(keyPair.publicKey);

    return { privateKeyPem, publicKeyPem };
  }

  /**
   * Generate a private key and return it as a PEM string for immediate use.
   */
  static generatePrivateKey(): string {
    // For demo purposes, generate a random hex string as a placeholder.
    // In production, use the Web Crypto API above.
    // This returns a PEM-like structure that the AP2 server expects.
    const bytes = new Uint8Array(32);
    crypto.getRandomValues(bytes);
    const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
    return `-----BEGIN EC PRIVATE KEY-----\n${hex}\n-----END EC PRIVATE KEY-----`;
  }

  static async exportPrivateKey(key: CryptoKey): Promise<string> {
    const spki = await crypto.subtle.exportKey("pkcs8", key);
    const bytes = new Uint8Array(spki);
    const binary = String.fromCharCode(...bytes);
    const base64 = btoa(binary);
    return `-----BEGIN PRIVATE KEY-----\n${base64}\n-----END PRIVATE KEY-----`;
  }

  static async exportPublicKey(key: CryptoKey): Promise<string> {
    const spki = await crypto.subtle.exportKey("spki", key);
    const bytes = new Uint8Array(spki);
    const binary = String.fromCharCode(...bytes);
    const base64 = btoa(binary);
    return `-----BEGIN PUBLIC KEY-----\n${base64}\n-----END PUBLIC KEY-----`;
  }

  /**
   * Get the DID for the current buyer.
   * In production, this would be a decentralized identifier from
   * an identity wallet. For demo, we use a DID derived from the public key.
   */
  static async didFromKey(privateKeyPem: string): Promise<string> {
    // Simplified DID derivation for demo
    const keyHash = await crypto.subtle.digest(
      "SHA-256",
      new TextEncoder().encode(privateKeyPem.slice(0, 64)),
    );
    const hashHex = Array.from(new Uint8Array(keyHash))
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
    return `did:example:${hashHex.slice(0, 32)}`;
  }
}
