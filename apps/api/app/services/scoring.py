"""Lead scoring logic - transparent and tunable"""
from typing import Dict, List, Tuple
from datetime import datetime, timedelta


class LeadScorer:
    """Rule-based lead scoring v1"""

    # Weights (must sum to 100)
    WEIGHT_FIT = 40  # location, type, beds/size match
    WEIGHT_BUDGET = 25  # budget alignment
    WEIGHT_INTENT = 20  # timeline urgency and specificity
    WEIGHT_READINESS = 15  # contact validity, pre-approval

    def score_lead(
        self,
        profile: Dict,
        top_matches: List[Dict],
        contact: Dict,
    ) -> Tuple[int, List[str]]:
        """
        Score a lead 0-100 with breakdown.
        Returns (score, reasons)
        """
        reasons = []
        total_score = 0

        # 1. Fit score (40%)
        fit_score = self._score_fit(profile, top_matches)
        total_score += fit_score
        if fit_score >= 30:
            reasons.append(f"Strong property match ({fit_score}/40)")
        elif fit_score >= 20:
            reasons.append(f"Moderate property match ({fit_score}/40)")
        else:
            reasons.append(f"Weak property match ({fit_score}/40)")

        # 2. Budget score (25%)
        budget_score = self._score_budget(profile, top_matches)
        total_score += budget_score
        if budget_score >= 20:
            reasons.append(f"Budget well-aligned ({budget_score}/25)")
        elif budget_score >= 10:
            reasons.append(f"Budget partially aligned ({budget_score}/25)")
        else:
            reasons.append(f"Budget mismatch ({budget_score}/25)")

        # 3. Intent score (20%)
        intent_score = self._score_intent(profile)
        total_score += intent_score
        if intent_score >= 15:
            reasons.append(f"High urgency/specificity ({intent_score}/20)")
        elif intent_score >= 10:
            reasons.append(f"Moderate intent ({intent_score}/20)")
        else:
            reasons.append(f"Low urgency ({intent_score}/20)")

        # 4. Readiness score (15%)
        readiness_score = self._score_readiness(profile, contact)
        total_score += readiness_score
        if readiness_score >= 10:
            reasons.append(f"Ready to proceed ({readiness_score}/15)")
        else:
            reasons.append(f"Needs more prep ({readiness_score}/15)")

        return int(total_score), reasons

    def _score_fit(self, profile: Dict, top_matches: List[Dict]) -> int:
        """Score property fit (0-40)"""
        score = 0

        # Location match (0-20)
        if profile.get("city") and profile.get("areas"):
            score += 15  # Has specific location preferences
            if len(top_matches) > 0:
                score += 5  # Found matching units
        elif profile.get("city"):
            score += 10

        # Type/beds/size match (0-20)
        if profile.get("property_type"):
            score += 5
        if profile.get("beds"):
            score += 5
        if profile.get("min_size_m2"):
            score += 5
        if len(top_matches) >= 3:
            score += 5  # Multiple good matches

        return min(score, 40)

    def _score_budget(self, profile: Dict, top_matches: List[Dict]) -> int:
        """Score budget alignment (0-25)"""
        budget_min = profile.get("budget_min", 0)
        budget_max = profile.get("budget_max", 0)

        if not budget_max:
            return 5  # No budget specified

        score = 10  # Has budget

        # Check if matches fall within budget
        in_budget = 0
        for match in top_matches[:5]:
            price = match.get("price", 0)
            if budget_min <= price <= budget_max:
                in_budget += 1

        if in_budget >= 3:
            score += 15  # Most matches in budget
        elif in_budget >= 1:
            score += 10  # Some matches in budget
        else:
            score += 0  # No matches in budget (red flag)

        return min(score, 25)

    def _score_intent(self, profile: Dict) -> int:
        """Score intent/urgency (0-20)"""
        score = 0

        # Timeline urgency (0-12)
        move_in = profile.get("move_in_date", "")
        if "immediate" in move_in.lower() or "asap" in move_in.lower():
            score += 12
        elif "month" in move_in.lower() or "60 days" in move_in.lower():
            score += 10
        elif "quarter" in move_in.lower() or "90 days" in move_in.lower():
            score += 6
        elif move_in:
            score += 3

        # Specificity (0-8)
        specificity = sum([
            bool(profile.get("property_type")),
            bool(profile.get("beds")),
            bool(profile.get("areas")),
            bool(profile.get("preferences")),
        ])
        score += specificity * 2

        return min(score, 20)

    def _score_readiness(self, profile: Dict, contact: Dict) -> int:
        """Score readiness (0-15)"""
        score = 0

        # Contact validity (0-8)
        if contact.get("email"):
            score += 4
        if contact.get("phone"):
            score += 4

        # Pre-approval (0-7)
        if profile.get("preapproved"):
            score += 7
        elif profile.get("financing_notes"):
            score += 3

        return min(score, 15)


# Singleton instance
lead_scorer = LeadScorer()
