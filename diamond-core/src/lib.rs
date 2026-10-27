#!forbid(unsafe_code)
// Tracked style debt — capability/transition APIs take more than 7 args by design.
// Reshape into request structs later; do not silence the whole crate.

pub mod authority;
pub mod hash;
pub mod identity;
pub mod provenance;
pub mod store;
pub mod transition;
pub mod types;
pub mod window;

pub use types::{AccessError, AccessRequest, AuthorityState, Capability, CapabilityId, Decision, Hash, MemoryObject, MemoryWindow, ObjectId, ObjectMeta, Operation, PolicyId, Provenance, ScarEvent, ScarSnapshot, SubjectId, TransitionId, TransitionRecord, Core};pub use authority::can_access;
pub use hash::hash_bytes;
pub use identity::compute_object_id;
pub use provenance::{compute_provenance_root, merkle_root, provenance_commitment};pub use transition::valid_promotion;
pub use window::window_contains_all;

pub fn now_seconds() -> u64 { std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap_or_default().as_secs() }

#[cfg(test)]
mod tests;
