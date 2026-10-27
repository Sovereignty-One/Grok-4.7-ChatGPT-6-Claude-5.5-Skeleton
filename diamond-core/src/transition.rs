use crate::{hash::hash_concat, types::*};

pub fn valid_promotion(prev:&AuthorityState,next:&AuthorityState)->bool { matches!((prev,next),(AuthorityState::ModelGenerated,AuthorityState::Unverified)|(AuthorityState::Unverified,AuthorityState::Reviewed)|(AuthorityState::Reviewed,AuthorityState::PolicyApproved)|(AuthorityState::PolicyApproved,AuthorityState::Authoritative)) }
pub fn transition_id(subject:SubjectId,policy:PolicyId,source:ObjectId,destination:ObjectId,timestamp:u64,from:AuthorityState,to:AuthorityState,evidence:Hash,proof:Hash)->TransitionId { hash_concat(&[&subject,&policy,&source,&destination,&timestamp.to_be_bytes(),&[from as u8,to as u8],&evidence,&proof]) }
impl Core {
    pub fn transition(&mut self,subject:SubjectId,id:ObjectId,to:AuthorityState,evidence_hash:Hash,authorization_proof:Hash,now:u64,capability_id:CapabilityId)->Result<ObjectId,AccessError>{
        let current=self.objects.get(&id).ok_or(AccessError::IdentityMismatch)?.clone();
        if !valid_promotion(&current.authority_state,&to){return Err(AccessError::InvalidTransition);}
        self.access(&AccessRequest{subject,object_id:id,operation:Operation::Promote,context_hash:current.meta.context_hash,epoch:self.epoch},capability_id,now)?;
        let p=Provenance{parent_object_ids:vec![id],evidence_hash,source_system:"diamond-core:authority-transition".into()};
        let mut next=current.next_version(&current.payload,p,self.epoch); next.authority_state=to; let dest=next.id; self.insert(next)?;
        let tid=transition_id(subject,self.policy_hash,id,dest,now,current.authority_state,to,evidence_hash,authorization_proof);
        self.scar.push(ScarEvent{transition:TransitionRecord{transition_id:tid,subject,policy_id:self.policy_hash,source_object:id,destination_object:dest,timestamp:now,previous_state:current.authority_state,new_state:to,evidence_hash,authorization_proof}}); Ok(dest)
    }
}
