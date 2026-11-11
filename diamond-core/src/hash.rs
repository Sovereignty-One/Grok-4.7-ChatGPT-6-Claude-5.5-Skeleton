use blake3::Hasher;
use crate::types::Hash;

pub fn hash_bytes(data: &[u8]) -> Hash {
    *blake3::hash(data).as_bytes()
}

pub fn hash_concat(parts: &[&[u8]]) -> Hash {
    let mut h = Hasher::new();
    for p in parts {
        h.update(&(p.len() as u64).to_be_bytes());
        h.update(p);
    }
    *h.finalize().as_bytes()
}

pub(crate) fn put_bytes(h: &mut Hasher, b: &[u8]) {
    h.update(&(b.len() as u64).to_be_bytes());
    h.update(b);
}
