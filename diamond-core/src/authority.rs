use crate::{hash::hash_concat, types::*};impl Capability {
    pub fn id(&self) -> CapabilityId { self.id }
    pub fn expiration(&self) -> u64 { self.expiration }
    pub fn revoked(&self) -> bool { self.revoked }
}

pub fn can_access(
    cap: &Capability,
    req: &AccessRequest,
    now: u64,
    policy_hash: PolicyId,
    current_epoch: u64,
) -> bool {
    !cap.revoked
        && cap.subject == req.subject
        && cap.object_scope.contains(&req.object_id)
        && cap.allowed_operations.contains(&req.operation)
        && cap.context_hash == req.context_hash
        && cap.epoch == req.epoch
        && cap.epoch == current_epoch
        && cap.policy_hash == policy_hash
        && cap.issued_at <= now
        && now < cap.expiration
        && !matches!(req.operation, Operation::Export)
}

pub fn capability_id(
    subject: SubjectId,
    ids: &std::collections::BTreeSet<ObjectId>,
    ops: &std::collections::BTreeSet<Operation>,
    context: Hash,
    issued: u64,
    expiration: u64,
    epoch: u64,
    policy: PolicyId,
) -> CapabilityId {
    let mut parts: Vec<Vec<u8>> = vec![b"DL5D-CAP-V1".to_vec(), subject.to_vec()];
    for id in ids {
        parts.push(id.to_vec())
    }
    for op in ops {
        parts.push(vec![*op as u8])
    }
    parts.push(context.to_vec());
    parts.push(issued.to_be_bytes().to_vec());
    parts.push(expiration.to_be_bytes().to_vec());
    parts.push(epoch.to_be_bytes().to_vec());
    parts.push(policy.to_vec());
    let refs: Vec<&[u8]> = parts.iter().map(Vec::as_slice).collect();
    hash_concat(&refs)
}
