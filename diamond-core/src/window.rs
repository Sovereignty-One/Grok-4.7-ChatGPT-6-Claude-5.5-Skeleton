use crate::types::*;
use blake3::Hasher;
use std::collections::BTreeSet;

pub fn window_contains_all(window: &MemoryWindow, visible: impl IntoIterator<Item = ObjectId>) -> bool {
    visible.into_iter().all(|id| window.object_ids.contains(&id))
}

pub fn make_window(
    _subject: SubjectId,
    ids: BTreeSet<ObjectId>,
    maximum_bytes: u64,
    context_hash: Hash,
    capability_id: CapabilityId,
    expiration: u64,
) -> MemoryWindow {
    let mut h = Hasher::new();
    h.update(b"DL5D-WINDOW-V1");
    for id in &ids {
        h.update(id);
    }
    h.update(&maximum_bytes.to_be_bytes());
    h.update(&context_hash);
    h.update(&capability_id);
    h.update(&expiration.to_be_bytes());
    let window_id = *h.finalize().as_bytes();

    MemoryWindow {
        window_id,
        object_ids: ids,
        maximum_bytes,
        context_hash,
        capability_id,
        expiration,
    }
}

impl MemoryWindow {
    pub fn capability_id(&self) -> CapabilityId {
        self.capability_id
    }
}
