use blake3::Hasher;
use crate::{hash::{hash_bytes, put_bytes}, provenance::provenance_commitment, types::*};

pub fn compute_object_id(meta: &ObjectMeta) -> ObjectId { derive_object_id(&meta.namespace, &meta.object_uuid, meta.content_hash, meta.version, meta.provenance_root) }
pub fn derive_object_id(namespace: &str, uuid: &str, content_hash: Hash, version: u64, provenance_root: Hash) -> ObjectId { let mut h=Hasher::new(); h.update(b"DL5D-OBJECT-V1"); put_bytes(&mut h, namespace.as_bytes()); put_bytes(&mut h, uuid.as_bytes()); h.update(&content_hash); h.update(&version.to_be_bytes()); h.update(&provenance_root); *h.finalize().as_bytes() }
impl MemoryObject {
    pub fn new(namespace: &str, uuid: &str, content: &[u8], version: u64, context_hash: Hash, epoch: u64, provenance: Provenance) -> Self { let content_hash=hash_bytes(content); let root=provenance_commitment(&provenance); let id=derive_object_id(namespace,uuid,content_hash,version,root); Self{id,meta:ObjectMeta{namespace:namespace.into(),object_uuid:uuid.into(),content_hash,version,provenance_root:root,context_hash,temporal_epoch:epoch,valid_from:0,valid_until:u64::MAX},provenance,authority_state:AuthorityState::Unverified,payload:content.to_vec()} }
    pub fn canonical_id(&self) -> ObjectId { compute_object_id(&self.meta) }
    pub fn next_version(&self, content: &[u8], provenance: Provenance, epoch: u64) -> Self { Self::new(&self.meta.namespace,&self.meta.object_uuid,content,self.meta.version+1,self.meta.context_hash,epoch,provenance) }
}
