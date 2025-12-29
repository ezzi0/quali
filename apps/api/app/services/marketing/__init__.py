"""Marketing services for the Marketing Agent"""

from .persona_discovery import PersonaDiscoveryService
from .creative_generator import CreativeGeneratorService
from .budget_optimizer import BudgetOptimizerService
from .attribution import AttributionService
from .platform_selector import PlatformSelectorService, PlatformScore, PlatformRecommendation
from .cross_platform_optimizer import (
    CrossPlatformOptimizer,
    PlatformBudgetAllocation,
    CrossPlatformRecommendation
)
from .learning_service import (
    LearningService,
    CreativePerformance,
    PersonaInsight,
    LearningCycleResult
)
from .lead_persona_matcher import LeadPersonaMatcherService, PersonaMatch
from .audience_sync import AudienceSyncService, AudienceSyncResult
from .experiment_runner import (
    ExperimentRunnerService,
    VariantResult,
    ExperimentResult
)

__all__ = [
    # Core services
    "PersonaDiscoveryService",
    "CreativeGeneratorService",
    "BudgetOptimizerService",
    "AttributionService",
    
    # Platform selection
    "PlatformSelectorService",
    "PlatformScore",
    "PlatformRecommendation",
    
    # Cross-platform optimization
    "CrossPlatformOptimizer",
    "PlatformBudgetAllocation",
    "CrossPlatformRecommendation",
    
    # Learning
    "LearningService",
    "CreativePerformance",
    "PersonaInsight",
    "LearningCycleResult",
    
    # Lead matching
    "LeadPersonaMatcherService",
    "PersonaMatch",
    
    # Audience sync
    "AudienceSyncService",
    "AudienceSyncResult",
    
    # Experiments
    "ExperimentRunnerService",
    "VariantResult",
    "ExperimentResult",
]
