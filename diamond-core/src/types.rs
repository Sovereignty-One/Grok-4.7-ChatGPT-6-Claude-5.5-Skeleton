use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};

pub type Hash = [u8; 32];
pub type ObjectId = Hash;
pub type CapabilityId = Hash;
pub type PolicyId = Hash;
pub type SubjectId = Hash;
pub type TransitionId = Hash;

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
pub enum AuthorityState { ModelGenerated, Unverified, Reviewed, PolicyApproved, Authoritative }

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Operation { Read, Create, Derive, Transform, Promote, Export, Share, Revoke, Delete }

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Decision { Allow, Deny, Audit }

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum AccessStage { Identity, Temporal, Context, Provenance, Authority }

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum AccessError { IdentityMismatch, TemporalMismatch, ContextMismatch, ProvenanceMismatch, AuthorityDenied, WindowExpired, ByteLimitExceeded, InvalidTransition, InvalidCapability }

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct Provenance { pub parent_object_ids: Vec<ObjectId>, pub evidence_hash: Hash, pub source_system: String }

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct ObjectMeta { pub namespace: String, pub object_uuid: String, pub content_hash: Hash, pub version: u64, pub provenance_root: Hash, pub context_hash: Hash, pub temporal_epoch: u64, pub valid_from: u64, pub valid_until: u64 }

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct MemoryObject { pub id: ObjectId, pub meta: ObjectMeta, pub provenance: Provenance, pub authority_state: AuthorityState, pub payload: Vec<u8> }

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Capability { pub id: CapabilityId, pub subject: SubjectId, pub object_scope: BTreeSet<ObjectId>, pub allowed_operations: BTreeSet<Operation>, pub context_hash: Hash, pub issued_at: u64, pub expiration: u64, pub epoch: u64, pub policy_hash: PolicyId, pub revoked: bool }

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct AccessRequest { pub subject: SubjectId, pub object_id: ObjectId, pub operation: Operation, pub context_hash: Hash, pub epoch: u64 }

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct MemoryWindow { pub window_id: Hash, pub object_ids: BTreeSet<ObjectId>, pub maximum_bytes: u64, pub context_hash: Hash, pub capability_id: CapabilityId, pub expiration: u64 }

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct TransitionRecord { pub transition_id: TransitionId, pub subject: SubjectId, pub policy_id: PolicyId, pub source_object: ObjectId, pub destination_object: ObjectId, pub timestamp: u64, pub previous_state: AuthorityState, pub new_state: AuthorityState, pub evidence_hash: Hash, pub authorization_proof: Hash }

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ScarEvent { pub transition: TransitionRecord }
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ScarSnapshot { pub root: Hash, pub epoch: u64 }

pub struct Core { pub(crate) objects: BTreeMap<ObjectId, MemoryObject>, pub(crate) capabilities: BTreeMap<CapabilityId, Capability>, pub(crate) epoch: u64, pub(crate) policy_hash: PolicyId, pub scar: Vec<ScarEvent>, pub scar_snapshots: Vec<ScarSnapshot> }

impl Default for Core { fn default() -> Self { Self::new([0; 32]) } }
impl Core { pub fn new(policy_hash: PolicyId) -> Self { Self { objects:BTreeMap::new(), capabilities:BTreeMap::new(), epoch:1, policy_hash, scar:vec![], scar_snapshots:vec![] } } pub fn epoch(&self)->u64{self.epoch} pub fn policy_hash(&self)->PolicyId{self.policy_hash} pub fn object(&self,id:&ObjectId)->Option<&MemoryObject>{self.objects.get(id)} }
