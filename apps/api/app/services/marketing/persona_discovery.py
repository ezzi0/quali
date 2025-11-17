"""
Persona Discovery Service

Discovers marketing personas through clustering analysis on lead profiles
and behavioral data, with LLM-based labeling and characterization.
"""
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import HDBSCAN, KMeans
from sqlalchemy.orm import Session
from sqlalchemy import select
from openai import OpenAI

from ...config import get_settings
from ...logging import get_logger
from ...models import Lead, LeadProfile, Qualification, Persona

settings = get_settings()
logger = get_logger(__name__)


class PersonaDiscoveryService:
    """
    Discovers marketing personas from lead data using clustering + LLM.
    
    Process:
    1. Extract features from leads (budget, location, urgency, etc.)
    2. Normalize and cluster using HDBSCAN
    3. Use LLM to label clusters with personas
    4. Generate messaging and positioning
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
    
    def discover_personas(
        self,
        min_cluster_size: int = 25,
        min_samples: int = 5,
        method: str = "hdbscan"
    ) -> List[Persona]:
        """
        Run persona discovery on all qualified leads.
        
        Args:
            min_cluster_size: Minimum size for a cluster to be considered a persona
            min_samples: Minimum samples for HDBSCAN core points
            method: 'hdbscan' or 'kmeans'
        
        Returns:
            List of discovered Persona objects
        """
        logger.info("persona_discovery_started", method=method)
        
        # 1. Fetch leads with profiles and qualifications
        leads_data = self._fetch_leads_for_clustering()
        
        if len(leads_data) < min_cluster_size * 2:
            logger.warning("insufficient_data", lead_count=len(leads_data))
            return []
        
        # 2. Feature extraction
        df = pd.DataFrame(leads_data)
        features, feature_names = self._extract_features(df)
        
        # 3. Clustering
        if method == "hdbscan":
            clusters = self._cluster_hdbscan(features, min_cluster_size, min_samples)
        else:
            n_clusters = max(3, len(leads_data) // 50)  # Auto-determine cluster count
            clusters = self._cluster_kmeans(features, n_clusters)
        
        # 4. Generate personas from clusters
        personas = []
        unique_clusters = np.unique(clusters[clusters >= 0])  # Exclude noise (-1)
        
        for cluster_id in unique_clusters:
            cluster_mask = clusters == cluster_id
            cluster_leads = df[cluster_mask]
            
            if len(cluster_leads) < min_cluster_size:
                continue
            
            persona = self._generate_persona_from_cluster(
                cluster_id=int(cluster_id),
                cluster_data=cluster_leads,
                feature_names=feature_names
            )
            
            if persona:
                personas.append(persona)
        
        logger.info("persona_discovery_completed", personas_found=len(personas))
        
        return personas
    
    def _fetch_leads_for_clustering(self) -> List[Dict[str, Any]]:
        """Fetch qualified leads with profiles and scores"""
        stmt = (
            select(Lead, LeadProfile, Qualification)
            .join(LeadProfile, Lead.id == LeadProfile.lead_id, isouter=True)
            .join(Qualification, Lead.id == Qualification.lead_id, isouter=True)
            .where(Qualification.qualified == True)
        )
        
        results = self.db.execute(stmt).all()
        
        leads_data = []
        for lead, profile, qualification in results:
            if not profile:
                continue
            
            leads_data.append({
                "lead_id": lead.id,
                "persona": lead.persona.value if lead.persona else "unknown",
                "source": lead.source.value,
                "city": profile.city,
                "areas": profile.areas or [],
                "property_type": profile.property_type,
                "beds": profile.beds or 0,
                "budget_min": float(profile.budget_min) if profile.budget_min else 0,
                "budget_max": float(profile.budget_max) if profile.budget_max else 0,
                "move_in_date": profile.move_in_date,
                "preapproved": profile.preapproved or False,
                "score": qualification.score if qualification else 50,
                "preferences": profile.preferences or [],
            })
        
        return leads_data
    
    def _extract_features(self, df: pd.DataFrame) -> tuple[np.ndarray, List[str]]:
        """
        Extract numerical features for clustering.
        
        Features:
        - Budget (mid-point and range)
        - Property type (one-hot)
        - Bedrooms
        - Urgency (derived from move_in_date)
        - Pre-approval status
        - Qualification score
        """
        features = []
        feature_names = []
        
        # Budget features
        budget_mid = ((df['budget_min'] + df['budget_max']) / 2).fillna(0)
        budget_range = (df['budget_max'] - df['budget_min']).fillna(0)
        features.append(budget_mid.values.reshape(-1, 1))
        features.append(budget_range.values.reshape(-1, 1))
        feature_names.extend(['budget_mid', 'budget_range'])
        
        # Property type one-hot
        property_types = pd.get_dummies(df['property_type'], prefix='type')
        features.append(property_types.values)
        feature_names.extend(property_types.columns.tolist())
        
        # Bedrooms
        features.append(df['beds'].fillna(0).values.reshape(-1, 1))
        feature_names.append('beds')
        
        # Urgency (boolean)
        urgency = df['move_in_date'].apply(
            lambda x: 1 if x and 'immediately' in str(x).lower() else 0
        )
        features.append(urgency.values.reshape(-1, 1))
        feature_names.append('urgency')
        
        # Pre-approved
        features.append(df['preapproved'].astype(int).values.reshape(-1, 1))
        feature_names.append('preapproved')
        
        # Score
        features.append((df['score'] / 100).values.reshape(-1, 1))  # Normalize
        feature_names.append('score_normalized')
        
        # Concatenate and normalize
        X = np.concatenate(features, axis=1)
        X_scaled = StandardScaler().fit_transform(X)
        
        return X_scaled, feature_names
    
    def _cluster_hdbscan(
        self, 
        features: np.ndarray,
        min_cluster_size: int,
        min_samples: int
    ) -> np.ndarray:
        """Cluster using HDBSCAN (density-based)"""
        clusterer = HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            metric='euclidean'
        )
        labels = clusterer.fit_predict(features)
        
        logger.info("hdbscan_clustering", 
                   n_clusters=len(np.unique(labels[labels >= 0])),
                   n_noise=np.sum(labels == -1))
        
        return labels
    
    def _cluster_kmeans(self, features: np.ndarray, n_clusters: int) -> np.ndarray:
        """Cluster using K-Means"""
        clusterer = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = clusterer.fit_predict(features)
        
        logger.info("kmeans_clustering", n_clusters=n_clusters)
        
        return labels
    
    def _generate_persona_from_cluster(
        self,
        cluster_id: int,
        cluster_data: pd.DataFrame,
        feature_names: List[str]
    ) -> Optional[Persona]:
        """
        Use LLM to generate persona name, description, and messaging.
        """
        # Calculate cluster statistics
        stats = {
            "size": len(cluster_data),
            "avg_budget": float(cluster_data['budget_mid'].mean()) if 'budget_mid' in cluster_data else 0,
            "common_property_types": cluster_data['property_type'].value_counts().head(3).to_dict(),
            "common_areas": self._most_common_items(cluster_data['areas']),
            "avg_beds": float(cluster_data['beds'].mean()),
            "preapproval_rate": float(cluster_data['preapproved'].mean()),
            "avg_score": float(cluster_data['score'].mean()),
            "urgency_rate": float((cluster_data['move_in_date'].str.contains('immediately', case=False, na=False)).mean()),
        }
        
        # Generate persona via LLM
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a marketing strategist specializing in real estate.
Generate a persona profile from lead cluster statistics. Return JSON with:
{
  "name": "Descriptive persona name",
  "description": "2-3 sentence description",
  "hooks": ["3 compelling hooks"],
  "objections": {"objection": "rebuttal"},
  "tone": "recommended tone"
}"""
                    },
                    {
                        "role": "user",
                        "content": f"Cluster statistics:\n{stats}\n\nGenerate persona profile."
                    }
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            import json
            persona_profile = json.loads(response.choices[0].message.content)
            
            # Create Persona object
            persona = Persona(
                name=persona_profile.get("name", f"Persona {cluster_id}"),
                description=persona_profile.get("description", ""),
                version=1,
                status="draft",
                rules={
                    "budget_range": [
                        float(cluster_data['budget_min'].quantile(0.25)),
                        float(cluster_data['budget_max'].quantile(0.75))
                    ],
                    "property_types": list(stats["common_property_types"].keys()),
                    "locations": stats["common_areas"][:5],
                },
                characteristics={
                    "urgency": "high" if stats["urgency_rate"] > 0.5 else "medium",
                    "price_sensitivity": "low" if stats["preapproval_rate"] > 0.6 else "medium",
                    "decision_speed": "fast" if stats["urgency_rate"] > 0.5 else "moderate"
                },
                messaging={
                    "hooks": persona_profile.get("hooks", []),
                    "objections": persona_profile.get("objections", {}),
                    "tone": persona_profile.get("tone", "professional")
                },
                metrics={
                    "total_leads": stats["size"],
                    "avg_score": stats["avg_score"]
                },
                sample_size=stats["size"],
                confidence_score=min(100, stats["size"] / 10)  # Confidence based on sample size
            )
            
            self.db.add(persona)
            self.db.commit()
            
            logger.info("persona_generated", 
                       persona_id=persona.id,
                       name=persona.name,
                       sample_size=stats["size"])
            
            return persona
            
        except Exception as e:
            logger.error("persona_generation_failed", cluster_id=cluster_id, error=str(e))
            return None
    
    @staticmethod
    def _most_common_items(series_of_lists, top_n: int = 5) -> List[str]:
        """Get most common items from a series of lists"""
        all_items = []
        for items in series_of_lists:
            if items:
                all_items.extend(items)
        
        from collections import Counter
        counts = Counter(all_items)
        return [item for item, _ in counts.most_common(top_n)]

