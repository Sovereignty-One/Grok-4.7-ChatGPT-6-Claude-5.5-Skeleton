use crate::{
    authority::{can_access, capability_id},
    hash::hash_bytes,
    provenance::{merkle_root, provenance_commitment},
    types::*,
    window::make_window,
};
use blake3::Hasher;
use std::collections::BTreeSet;

impl Core {
    pub fn insert(&mut self, object: MemoryObject) -> Result<(), AccessError> {
        if object.meta.version == 0 || object.id != object.canonical_id() || object.meta.content_hash != hash_bytes(&object.payload) || object.meta.provenance_root != provenance_commitment(&object.provenance) { return Err(AccessError::IdentityMismatch); }
        if object.meta.temporal_epoch != self.epoch || self.objects.contains_key(&object.id) { return Err(AccessError::IdentityMismatch); }
        if object.provenance.parent_object_ids.iter().any(|p| !self.objects.contains_key(p)) { return Err(AccessError::ProvenanceMismatch); }
        self.objects.insert(object.id, object); Ok(())
    }

    pub fn issue_capability(&mut self, subject: SubjectId, object_scope: BTreeSet<ObjectId>, operations: BTreeSet<Operation>, context_hash: Hash, issued_at: u64, ttl_seconds: u64) -> CapabilityId {
        let expiration = issued_at.saturating_add(ttl_seconds);
        let id = capability_id(subject,&object_scope,&operations,context_hash,issued_at,expiration,self.epoch,self.policy_hash);
        self.capabilities.insert(id, Capability{id,subject,object_scope,allowed_operations:operations,context_hash,issued_at,expiration,epoch:self.epoch,policy_hash:self.policy_hash,revoked:false}); id
    }

    pub fn revoke_capability(&mut self, subject: SubjectId, id: CapabilityId) -> Result<(), AccessError> {
        let c = self.capabilities.get_mut(&id).ok_or(AccessError::InvalidCapability)?;
        if c.subject != subject { return Err(AccessError::AuthorityDenied); }
        c.revoked = true; Ok(())
    }

    pub fn access(&self, req:&AccessRequest, capability_id:CapabilityId, now:u64)->Result<Decision,AccessError>{
        let o=self.objects.get(&req.object_id).ok_or(AccessError::IdentityMismatch)?.clone();
        if o.id!=req.object_id || o.canonical_id()!=o.id{return Err(AccessError::IdentityMismatch);}
        if req.epoch!=self.epoch || o.meta.temporal_epoch!=req.epoch || now<o.meta.valid_from || now>o.meta.valid_until{return Err(AccessError::TemporalMismatch);}
        if o.meta.context_hash!=req.context_hash{return Err(AccessError::ContextMismatch);}
        if o.meta.provenance_root!=provenance_commitment(&o.provenance) || o.provenance.parent_object_ids.iter().any(|p|!self.objects.contains_key(p)){return Err(AccessError::ProvenanceMismatch);}
        let c=self.capabilities.get(&capability_id).ok_or(AccessError::InvalidCapability)?.clone();
        if !can_access(&c,req,now,self.policy_hash,self.epoch){return Err(AccessError::AuthorityDenied);} Ok(Decision::Allow)
    }

    pub fn window(&self,subject:SubjectId,ids:BTreeSet<ObjectId>,maximum_bytes:u64,context_hash:Hash,capability_id:CapabilityId,now:u64)->Result<MemoryWindow,AccessError>{
        let c=self.capabilities.get(&capability_id).ok_or(AccessError::InvalidCapability)?.clone();
        if c.subject!=subject || c.context_hash!=context_hash || c.revoked || now>=c.expiration{return Err(AccessError::WindowExpired);}
        for id in &ids { self.access(&AccessRequest{subject,object_id:*id,operation:Operation::Read,context_hash,epoch:self.epoch},capability_id,now)?; }
        Ok(make_window(subject,ids,maximum_bytes,context_hash,capability_id,c.expiration))
    }

    pub fn window_read(&self,subject:SubjectId,w:&MemoryWindow,id:ObjectId,bytes:u64,now:u64)->Result<Decision,AccessError>{
        if now>=w.expiration{return Err(AccessError::WindowExpired);} if !w.object_ids.contains(&id){return Err(AccessError::AuthorityDenied);} if bytes>w.maximum_bytes{return Err(AccessError::ByteLimitExceeded);}
        self.access(&AccessRequest{subject,object_id:id,operation:Operation::Read,context_hash:w.context_hash,epoch:self.epoch},w.capability_id,now)
    }

    pub fn snapshot_root(&self)->Hash{let leaves=self.objects.values().map(object_commitment).collect();merkle_root(leaves)}
    pub fn record_snapshot(&mut self)->Hash{let root=self.snapshot_root();self.scar_snapshots.push(ScarSnapshot{root,epoch:self.epoch});root}
    pub fn verify_snapshot(&self,expected:Hash)->bool{self.snapshot_root()==expected}
}

fn object_commitment(o:&MemoryObject)->Hash{let mut h=Hasher::new();h.update(b"DL5D-OBJECT-COMMIT-V1");h.update(&o.id);h.update(&o.meta.version.to_be_bytes());h.update(&o.meta.provenance_root);h.update(&o.meta.context_hash);h.update(&[o.authority_state as u8]);*h.finalize().as_bytes()}
