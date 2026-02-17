import json
import logging
from typing import Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)


class ComplianceMapper:
    """Map leakage findings to compliance framework violations."""

    # Compliance mappings per leakage type
    COMPLIANCE_MAPPINGS = {
        "cross_user": {
            "SOC2": ["CC6.1", "CC6.6", "CC6.7"],
            "ISO27001": ["A.9.2.1", "A.9.4.1"],
            "CPCSC": ["SA-4", "AC-3"],
            "NIST_AI_RMF": ["GOVERN-1.2", "MAP-2.3", "MEASURE-2.5"],
        },
        "training_data": {
            "SOC2": ["CC6.1", "CC7.2"],
            "ISO27001": ["A.9.2.1"],
            "CPCSC": ["SA-4"],
            "NIST_AI_RMF": ["MAP-2.3"],
        },
        "context_boundary": {
            "SOC2": ["CC6.6"],
            "ISO27001": ["A.9.4.1"],
            "CPCSC": ["AC-3"],
            "NIST_AI_RMF": ["MEASURE-2.5"],
        },
        "system_prompt": {
            "SOC2": ["CC6.1"],
            "ISO27001": ["A.9.2.1"],
            "CPCSC": ["SA-4"],
            "NIST_AI_RMF": ["GOVERN-1.2"],
        },
    }

    # Control descriptions
    CONTROL_DESCRIPTIONS = {
        "CC6.1": "Logical access security infrastructure and software",
        "CC6.6": "Encryption of data in transit and at rest",
        "CC6.7": "System monitoring and anomaly detection",
        "CC7.2": "System operations and monitoring",
        "A.9.2.1": "User registration and de-registration",
        "A.9.4.1": "Information access restriction",
        "SA-4": "System acquisition and security controls",
        "AC-3": "Access enforcement mechanisms",
        "GOVERN-1.2": "AI risk management governance",
        "MAP-2.3": "AI system categorization and risk assessment",
        "MEASURE-2.5": "AI system performance and risk monitoring",
    }

    def __init__(self, mappings_file: str = None):
        """Initialize with optional custom mappings file."""
        if mappings_file and Path(mappings_file).exists():
            with open(mappings_file, "r") as f:
                self.COMPLIANCE_MAPPINGS = json.load(f)

    def map_to_compliance(self, leakage_categories: List[str]) -> Dict:
        """
        Map leakage categories to compliance violations.

        Args:
            leakage_categories: List of detected leakage categories

        Returns:
            Dict mapping framework names to lists of violated controls
        """
        violations = {
            "SOC2": {"controls": [], "description": "Service Organization Control 2"},
            "ISO27001": {"controls": [], "description": "ISO/IEC 27001"},
            "CPCSC": {
                "controls": [],
                "description": "Canadian Protected/Controlled Signals Catalogue",
            },
            "NIST_AI_RMF": {
                "controls": [],
                "description": "NIST AI Risk Management Framework",
            },
        }

        for category in leakage_categories:
            if category in self.COMPLIANCE_MAPPINGS:
                mapping = self.COMPLIANCE_MAPPINGS[category]
                for framework, controls in mapping.items():
                    if framework in violations:
                        for control in controls:
                            if control not in violations[framework]["controls"]:
                                violations[framework]["controls"].append(control)

        # Add descriptions to each control
        for framework in violations:
            controls_with_desc = []
            for control in violations[framework]["controls"]:
                desc = self.CONTROL_DESCRIPTIONS.get(control, "")
                controls_with_desc.append({"control_id": control, "description": desc})
            violations[framework]["controls"] = controls_with_desc

        return violations

    def generate_remediation(self, leakage_category: str, risk_level: str) -> str:
        """
        Generate remediation guidance based on finding.

        Args:
            leakage_category: Type of leakage detected
            risk_level: Risk level (LOW, MEDIUM, HIGH, CRITICAL)

        Returns:
            Remediation text
        """
        remediations = {
            "cross_user": {
                "CRITICAL": (
                    "IMMEDIATE ACTION REQUIRED: Implement strict tenant isolation controls. "
                    "Review access controls, implement data segmentation, and audit all cross-user "
                    "data access mechanisms. Consider immediate vendor notification."
                ),
                "HIGH": (
                    "Urgent: Review and strengthen user data isolation mechanisms. "
                    "Implement additional access controls and monitoring for cross-user data access."
                ),
                "MEDIUM": (
                    "Review data isolation controls and ensure proper tenant separation. "
                    "Implement monitoring for anomalous cross-user access patterns."
                ),
                "LOW": (
                    "Continue monitoring cross-user access patterns. "
                    "Periodically review isolation controls as part of regular security assessments."
                ),
            },
            "training_data": {
                "CRITICAL": (
                    "IMMEDIATE ACTION REQUIRED: Suspend potentially compromised training pipelines. "
                    "Conduct full audit of data handling procedures and implement data anonymization."
                ),
                "HIGH": (
                    "Urgent: Review data retention and training data protection policies. "
                    "Implement data minimization and anonymization controls."
                ),
                "MEDIUM": (
                    "Review training data handling procedures. Ensure proper consent and data protection "
                    "measures are in place."
                ),
                "LOW": (
                    "Continue monitoring training data handling. Review policies periodically."
                ),
            },
            "context_boundary": {
                "CRITICAL": (
                    "IMMEDIATE ACTION REQUIRED: Audit all workspace/context boundaries. "
                    "Implement strict isolation controls and review multi-tenant architecture."
                ),
                "HIGH": (
                    "Urgent: Review context isolation mechanisms. Implement additional boundary controls."
                ),
                "MEDIUM": (
                    "Review workspace isolation controls. Ensure proper separation between contexts."
                ),
                "LOW": (
                    "Continue monitoring context boundaries. Periodic review recommended."
                ),
            },
            "system_prompt": {
                "CRITICAL": (
                    "IMMEDIATE ACTION REQUIRED: Review and harden system prompts. "
                    "Implement prompt injection protections and access controls."
                ),
                "HIGH": (
                    "Urgent: Review system prompt security. Implement controls to prevent prompt extraction."
                ),
                "MEDIUM": (
                    "Review system prompt handling. Ensure sensitive instructions are properly protected."
                ),
                "LOW": (
                    "Continue monitoring for system prompt leakage. Periodic security review recommended."
                ),
            },
        }

        category_remediations = remediations.get(leakage_category, {})
        return category_remediations.get(
            risk_level,
            "Review security controls and implement appropriate mitigations based on findings.",
        )
