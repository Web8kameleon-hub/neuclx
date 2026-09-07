use algebra::TideLevel;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum GovernanceDecision {
    Approved,
    Rejected,
    SandboxOnly,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GovernanceEnvelope {
    pub protocol_id: String,
    pub author_node: String,
    pub requires_self_learning: bool,
    pub requires_self_writing: bool,
    pub requested_scope: String,
    pub tide: String,
    pub ndb_quality: String,
    pub risk_score: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GovernanceAudit {
    pub decision: GovernanceDecision,
    pub reason: String,
    pub enforce_jona_sandbox: bool,
    pub allow_auto_promote: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JonaSandboxPolicy {
    pub min_ndb_quality_for_autopromote: String,
    pub max_risk_score_for_autopromote: f32,
    pub deny_autopromote_in_low_tide: bool,
}

impl Default for JonaSandboxPolicy {
    fn default() -> Self {
        Self {
            min_ndb_quality_for_autopromote: "good".to_string(),
            max_risk_score_for_autopromote: 0.35,
            deny_autopromote_in_low_tide: true,
        }
    }
}

impl GovernanceEnvelope {
    pub fn tide_level(&self) -> TideLevel {
        match self.tide.to_lowercase().as_str() {
            "high" => TideLevel::High,
            "low" => TideLevel::Low,
            _ => TideLevel::Normal,
        }
    }
}

pub fn evaluate_governance(
    envelope: &GovernanceEnvelope,
    policy: &JonaSandboxPolicy,
) -> GovernanceAudit {
    let tide = envelope.tide_level();
    let quality = envelope.ndb_quality.to_lowercase();

    if envelope.risk_score >= 0.85 {
        return GovernanceAudit {
            decision: GovernanceDecision::Rejected,
            reason: "risk score too high".to_string(),
            enforce_jona_sandbox: true,
            allow_auto_promote: false,
        };
    }

    if envelope.requires_self_writing || envelope.requires_self_learning {
        if tide == TideLevel::Low && policy.deny_autopromote_in_low_tide {
            return GovernanceAudit {
                decision: GovernanceDecision::SandboxOnly,
                reason: "low tide forces sandbox-only review".to_string(),
                enforce_jona_sandbox: true,
                allow_auto_promote: false,
            };
        }

        if envelope.risk_score > policy.max_risk_score_for_autopromote {
            return GovernanceAudit {
                decision: GovernanceDecision::SandboxOnly,
                reason: "risk score requires JONA sandbox review".to_string(),
                enforce_jona_sandbox: true,
                allow_auto_promote: false,
            };
        }

        if quality < policy.min_ndb_quality_for_autopromote {
            return GovernanceAudit {
                decision: GovernanceDecision::SandboxOnly,
                reason: "ndb quality below auto-promote threshold".to_string(),
                enforce_jona_sandbox: true,
                allow_auto_promote: false,
            };
        }
    }

    GovernanceAudit {
        decision: GovernanceDecision::Approved,
        reason: "governance checks passed".to_string(),
        enforce_jona_sandbox: false,
        allow_auto_promote: true,
    }
}

