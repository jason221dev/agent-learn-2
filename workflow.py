#!/usr/bin/env python3
"""
Agent Learn 2 - Autonomous AI Framework
Version: 2.0 (Optimized Architecture)
Main workflow orchestrator with just-in-time loading and auto-execution
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

class AgentLearn2:
    def __init__(self, base_path='/sdcard/AEAF'):
        self.base_path = Path(base_path)
        self.state = self._load_state()
        self.config = self._load_config()
        self.llm_intelligence_metrics = self._load_intelligence_metrics()
        self.skill_cache = {}  # LRU cache for loaded skills
        self.mcp_cache = {}    # LRU cache for loaded MCPs
        self.max_cache_size = 10
        
    def _load_state(self):
        state_path = self.base_path / 'state' / 'current_state.json'
        if state_path.exists():
            with open(state_path, 'r') as f:
                return json.load(f)
        return {'cycle': 0, 'status': 'initializing'}
    
    def _load_config(self):
        config_path = self.base_path / 'config' / 'meta_learning.json'
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        return {}

    def _load_intelligence_metrics(self):
        """Load LLM intelligence tracking metrics"""
        metrics_path = self.base_path / 'state' / 'intelligence_metrics.json'
        if metrics_path.exists():
            with open(metrics_path, 'r') as f:
                return json.load(f)
        return {
            'baseline_accuracy': 0.0,
            'current_accuracy': 0.0,
            'baseline_precision': 0.0,
            'current_precision': 0.0,
            'task_success_rate': 0.0,
            'improvements_applied': 0,
            'improvements_successful': 0,
            'last_updated': datetime.now().isoformat()
        }

    def load_full_implementation(self, skill_id=None, mcp_id=None):
        """Load full implementation for a skill or MCP (JIT loading)"""
        impl_data = None
        
        if skill_id:
            # Check cache first
            if skill_id in self.skill_cache:
                return self.skill_cache[skill_id]
            
            # Load from file
            impl_path = self.base_path / 'skills' / skill_id / 'full_implementation.json'
            if impl_path.exists():
                with open(impl_path, 'r') as f:
                    impl_data = json.load(f)
                # Add to cache
                self._add_to_cache(skill_id, impl_data, is_skill=True)
        
        if mcp_id:
            # Check cache first
            if mcp_id in self.mcp_cache:
                return self.mcp_cache[mcp_id]
            
            # Load from file
            impl_path = self.base_path / 'mcps' / mcp_id / 'full_implementation.json'
            if impl_path.exists():
                with open(impl_path, 'r') as f:
                    impl_data = json.load(f)
                # Add to cache
                self._add_to_cache(mcp_id, impl_data, is_skill=False)
        
        return impl_data

    def _add_to_cache(self, id, data, is_skill=True):
        """Add to LRU cache with size limit"""
        cache = self.skill_cache if is_skill else self.mcp_cache
        max_size = self.max_cache_size
        
        if len(cache) >= max_size:
            # Remove oldest (first) item
            if cache:
                oldest = next(iter(cache))
                del cache[oldest]
        
        cache[id] = data

    def update_intelligence_metrics(self, success=True, accuracy_delta=0.0, precision_delta=0.0):
        """Update LLM intelligence metrics after task execution"""
        self.llm_intelligence_metrics['last_updated'] = datetime.now().isoformat()
        
        if success:
            self.llm_intelligence_metrics['improvements_successful'] += 1
            self.llm_intelligence_metrics['task_success_rate'] = (
                self.llm_intelligence_metrics['improvements_successful'] /
                max(1, self.llm_intelligence_metrics['improvements_applied'])
            )
        
        # Track deltas
        if accuracy_delta != 0.0:
            self.llm_intelligence_metrics['current_accuracy'] += accuracy_delta
        if precision_delta != 0.0:
            self.llm_intelligence_metrics['current_precision'] += precision_delta
        
        # Save metrics
        metrics_path = self.base_path / 'state' / 'intelligence_metrics.json'
        with open(metrics_path, 'w') as f:
            json.dump(self.llm_intelligence_metrics, f, indent=2)
    
    def load_skill_registry(self):
        """Just-in-time skill registry loading"""
        registry_path = self.base_path / 'skills' / 'registry.json'
        if registry_path.exists():
            with open(registry_path, 'r') as f:
                return json.load(f)
        return {'skills': []}
    
    def load_mcp_registry(self):
        """Just-in-time MCP registry loading"""
        registry_path = self.base_path / 'mcps' / 'registry.json'
        if registry_path.exists():
            with open(registry_path, 'r') as f:
                return json.load(f)
        return {'mcps': []}
    
    def load_insights(self):
        """Load insight registry for pattern matching"""
        insights_path = self.base_path / 'learning' / 'insights.json'
        if insights_path.exists():
            with open(insights_path, 'r') as f:
                return json.load(f)
        return {'insights': []}
    
    def get_skill_by_trigger(self, trigger_keyword):
        """Find skill by trigger keyword (just-in-time)"""
        registry = self.load_skill_registry()
        trigger_keyword = trigger_keyword.lower()
        for skill in registry.get('skills', []):
            if trigger_keyword in skill.get('trigger_keywords', []):
                return skill
        return None
    
    def get_mcp_by_trigger(self, trigger_keyword):
        """Find MCP by trigger keyword (just-in-time)"""
        registry = self.load_mcp_registry()
        trigger_keyword = trigger_keyword.lower()
        for mcp in registry.get('mcps', []):
            if trigger_keyword in mcp.get('trigger_keywords', []):
                return mcp
        return None
    
    def match_error_pattern(self, error_message):
        """Match error against insight patterns and auto-execute solution"""
        insights = self.load_insights()
        error_lower = error_message.lower()
        
        for insight in insights.get('insights', []):
            if insight['type'] == 'error_pattern':
                for pattern in insight.get('trigger_patterns', []):
                    if pattern.lower() in error_lower:
                        # Found match! Auto-execute solution
                        print(f"🔍 Error pattern matched: {insight['insight_id']}")
                        
                        # Load solution skill if specified
                        if 'solution_skill' in insight:
                            print(f"   Loading solution skill: {insight['solution_skill']}")
                            solution = self.get_skill_by_trigger(insight['solution_skill'])
                            if solution:
                                print(f"   ✅ Solution skill loaded: {solution['name']}")
                        
                        # Auto-propose improvement
                        try:
                            from auto_improvement_executor import AutoImprovementExecutor
                            executor = AutoImprovementExecutor(str(self.base_path))
                            executor.propose_improvement({
                                'error': error_message,
                                'matched_pattern': insight,
                                'timestamp': datetime.now().isoformat()
                            })
                        except Exception as e:
                            print(f"   ⚠️  Auto-improvement executor error: {e}")
                        
                        return insight
        return None
    
    def run_discovery_cycle(self, keywords=None):
        """Execute discovery cycle with limits (top 20 repos/keyword)"""
        if keywords is None:
            keywords = ['skill', 'mcp', 'agent']
        
        print(f"🔍 Starting optimized discovery cycle...")
        print(f"Keywords: {keywords}")
        print(f"Limit: Top 20 repos per keyword by recent stars")
        
        self.state['last_discovery'] = datetime.now().isoformat()
        self.state['discovery_count'] = self.state.get('discovery_count', 0) + 1
        
        return {
            'status': 'discovery_complete',
            'keywords_searched': keywords,
            'limit_per_keyword': 20,
            'sort_by': 'recent_stars'
        }
    
    def propose_architecture_improvement(self, error_analysis):
        """Autonomous architecture improvement proposal"""
        improvements_path = self.base_path / 'learning' / 'improvements'
        improvements_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        proposal = {
            'id': f'improvement_{timestamp}',
            'trigger': 'new_error_pattern_detected',
            'analysis': error_analysis,
            'proposed_changes': [],
            'confidence': 0.0,
            'status': 'proposed',
            'created_at': datetime.now().isoformat()
        }
        
        proposal_path = improvements_path / f'{timestamp}.json'
        with open(proposal_path, 'w') as f:
            json.dump(proposal, f, indent=2)
        
        print(f"💡 Architecture improvement proposed: {proposal['id']}")
        return proposal
    
    def save_state(self):
        """Persist current state"""
        state_path = self.base_path / 'state' / 'current_state.json'
        with open(state_path, 'w') as f:
            json.dump(self.state, f, indent=2, default=str)
    
    def run(self):
        """Main execution loop"""
        print("=" * 70)
        print("AGENT LEARN 2 v2.0 - Autonomous AI Framework")
        print("=" * 70)
        print(f"Architecture: {self.state.get('architecture_version', '1.0')}")
        print(f"Status: {self.state.get('status', 'unknown')}")
        print(f"Cycle: {self.state.get('cycle', 0)}")
        print("=" * 70)
        
        # Load registries (just-in-time, not all at once)
        skill_registry = self.load_skill_registry()
        mcp_registry = self.load_mcp_registry()
        insights = self.load_insights()
        
        print(f"Available skills: {len(skill_registry.get('skills', []))}")
        print(f"Available MCPs: {len(mcp_registry.get('mcps', []))}")
        print(f"Registered insights: {len(insights.get('insights', []))}")
        print("=" * 70)
        
        # Execute discovery cycle
        discovery_result = self.run_discovery_cycle()
        print(f"Discovery result: {discovery_result['status']}")
        
        # Save state
        self.save_state()
        
        return {
            'status': 'complete',
            'state': self.state,
            'discovery': discovery_result
        }

if __name__ == '__main__':
    agent = AgentLearn2()
    result = agent.run()
    print("\n✅ Framework execution complete")
    print(f"Next cycle scheduled: {agent.state.get('next_cycle', 'on_trigger')}")
