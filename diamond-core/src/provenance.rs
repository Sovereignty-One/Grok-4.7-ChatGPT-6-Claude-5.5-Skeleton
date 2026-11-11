use blake3::Hasher;
use crate::{hash::{hash_bytes, put_bytes}, types::*};

pub fn compute_provenance_root(p: &Provenance) -> Hash { let mut h=Hasher::new(); put_bytes(&mut h,p.source_system.as_bytes()); h.update(&(p.parent_object_ids.len() as u64).to_be_bytes()); for id in &p.parent_object_ids { h.update(id); } h.update(&p.evidence_hash); *h.finalize().as_bytes() }
pub fn provenance_commitment(p:&Provenance)->Hash { compute_provenance_root(p) }
pub fn merkle_root(mut leaves:Vec<Hash>)->Hash { if leaves.is_empty(){return hash_bytes(b"")} leaves.sort(); while leaves.len()>1 { let mut next=Vec::with_capacity((leaves.len()+1)/2); for pair in leaves.chunks(2) { let right=if pair.len()==2{pair[1]}else{pair[0]}; let mut h=Hasher::new(); h.update(b"DL5D-MERKLE"); h.update(&pair[0]); h.update(&right); next.push(*h.finalize().as_bytes()); } leaves=next; } leaves[0] }
