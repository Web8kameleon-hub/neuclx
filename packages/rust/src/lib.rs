#[derive(Clone,Copy,Debug,Eq,PartialEq)]
pub enum EvidenceState{Measured,Computed,Declared,Unavailable,NotImplemented}

#[derive(Clone,Copy,Debug,Eq,PartialEq)]
pub enum JonaDecision{Allow,SandboxOnly,Reject}

#[derive(Clone,Debug,Eq,PartialEq)]
pub struct Datum<T>{pub value:Option<T>,pub state:EvidenceState,pub source:Option<String>,pub method:Option<String>}

impl<T> Datum<T>{
    pub fn new(value:Option<T>,state:EvidenceState,source:Option<String>,method:Option<String>)->Result<Self,&'static str>{
        if matches!(state,EvidenceState::Measured|EvidenceState::Computed)&&method.is_none(){return Err("measured/computed requires method")}
        if state==EvidenceState::Measured&&source.is_none(){return Err("measured requires source")}
        if matches!(state,EvidenceState::Unavailable|EvidenceState::NotImplemented)&&value.is_some(){return Err("unavailable/not_implemented requires empty value")}
        Ok(Self{value,state,source,method})
    }
    pub fn jona_decision(&self)->JonaDecision{match self.state{EvidenceState::Declared=>JonaDecision::SandboxOnly,_=>JonaDecision::Allow}}
}

#[cfg(test)]mod tests{use super::*;
#[test]fn unavailable_rejects_hidden_value(){assert!(Datum::new(Some(42),EvidenceState::Unavailable,None,Some("none".into())).is_err())}
#[test]fn declared_stays_sandboxed(){let d=Datum::<()>::new(None,EvidenceState::Declared,None,None).unwrap();assert_eq!(d.jona_decision(),JonaDecision::SandboxOnly)}
}
