#!/usr/bin/env python3
"""
Auto-Improvement Executor v2.0
Automatically executes proposed improvements without user approval
With dynamic confidence calculation and rollback mechanism
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
import re

class AutoImprovementExecutor:
    def __init__(self, base_path='/sdcard/AEAF'):
        self.base_path = Path(base_path)
        self.config = self._load_config()
        self.rollback_dir = self.base_path / 'learning' / 'rollbacks'
        self.rollback_dir.mkdir(parents=True, exist_ok=True)
        
    def _load_config(self):
        config_path = self.base_path / 'config' / 'meta_learning.json'
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        return {}

    def calculate_dynamic_confidence(self, error_analysis):
        """Calculate confidence based on multiple factors"""
        confidence = 0.5  # Base confidence
        
        # Factor 1: Error severity (from pattern)
        matched_pattern = error_analysis.get('matched_pattern', {})
        pattern_confidence = matched_pattern.get('confidence', 0.5)
        confidence += pattern_confidence * 0.3  # 30% weight
        
        # Factor 2: Historical success rate for this pattern
        occurrences = matched_pattern.get('occurrences', 0)
        if occurrences > 10:
            confidence += 0.15  # High occurrence = more confidence
        elif occurrences > 5:
            confidence += 0.10
        elif occurrences > 0:
            confidence += 0.05
        
        # Factor 3: Solution skill availability
        solution_skill = matched_pattern.get('solution_skill')
        if solution_skill:
            # Check if solution skill exists in registry
            skills_path = self.base_path / 'skills' / 'registry.json'
            if skills_path.exists():
                with open(skills_path, 'r') as f:
                    skills = json.load(f)
                skill_exists = any(s['skill_id'] == solution_skill or s['name'] == solution_skill 
                                  for s in skills.get('skills', []))
                if skill_exists:
                    confidence += 0.05  # Solution available
        
        # Cap at 0.99
        return min(0.99, confidence)

    def create_rollback_point(self, improvement_id, affected_files=None):
        """Create rollback point before making changes"""
        rollback_point = {
            'improvement_id': improvement_id,
            'timestamp': datetime.now().isoformat(),
            'affected_files': affected_files or [],
            'backup_paths': []
        }
        
        # Backup affected files
        for file_path in (affected_files or []):
            src = Path(file_path)
            if src.exists():
                backup_name = f"{improvement_id}_{src.name}"
                backup_path = self.rollback_dir / backup_name
                shutil.copy2(src, backup_path)
                rollback_point['backup_paths'].append(str(backup_path))
        
        # Save rollback point
        rollback_path = self.rollback_dir / f"{improvement_id}_rollback.json"
        with open(rollback_path, 'w') as f:
            json.dump(rollback_point, f, indent=2)
        
        return rollback_path

    def rollback_improvement(self, improvement_id):
        """Rollback an improvement to previous state"""
        rollback_path = self.rollback_dir / f"{improvement_id}_rollback.json"
        if not rollback_path.exists():
            print(f"❌ No rollback point found for {improvement_id}")
            return False
        
        with open(rollback_path, 'r') as f:
            rollback_point = json.load(f)
        
        # Restore backed up files
        for backup_path in rollback_point.get('backup_paths', []):
            backup = Path(backup_path)
            if backup.exists():
                # Extract original filename
                original_name = backup.name.replace(f"{improvement_id}_", "")
                original_path = self.base_path / original_name
                shutil.copy2(backup, original_path)
        
        print(f"✅ Rolled back improvement: {improvement_id}")
        return True
    
    def check_and_execute(self):
        """Check for new improvements and auto-execute"""
        improvements_path = self.base_path / 'learning' / 'improvements'
        if not improvements_path.exists():
            return []
        
        executed = []
        for proposal_file in improvements_path.glob('*.json'):
            if 'auto_executed' in str(proposal_file):
                continue
                
            with open(proposal_file, 'r') as f:
                proposal = json.load(f)
            
            # Auto-execute if confidence > threshold
            threshold = self.config.get('architecture_improvements', {}).get('auto_implement_threshold', 0.7)
            
            if proposal.get('confidence', 0) >= threshold:
                print(f"🚀 Auto-executing: {proposal['id']}")
                self._execute_improvement(proposal, proposal_file)
                executed.append(proposal['id'])
        
        return executed
    
    def _execute_improvement(self, proposal, proposal_file):
        """Execute the improvement"""
        # Log execution
        log_path = self.base_path / 'learning' / 'improvements' / 'auto_executed.json'
        if log_path.exists():
            with open(log_path, 'r') as f:
                log = json.load(f)
        else:
            log = {'executed': []}
        
        proposal['executed_at'] = datetime.now().isoformat()
        proposal['status'] = 'auto_executed'
        log['executed'].append(proposal)
        
        with open(log_path, 'w') as f:
            json.dump(log, f, indent=2)
        
        # Update proposal file
        proposal_file_path = Path(proposal_file)
        proposal_data = {}
        if proposal_file_path.exists():
            with open(proposal_file_path, 'r') as f:
                proposal_data = json.load(f)
        proposal_data['status'] = 'auto_executed'
        proposal_data['executed_at'] = datetime.now().isoformat()
        with open(proposal_file_path, 'w') as f:
            json.dump(proposal_data, f, indent=2)
        
        print(f"   ✅ Executed: {proposal['id']}")
    
    def propose_improvement(self, error_analysis):
        """Propose and auto-execute an improvement with dynamic confidence"""
        improvements_path = self.base_path / 'learning' / 'improvements'
        improvements_path.mkdir(parents=True, exist_ok=True)

        # Calculate dynamic confidence based on multiple factors
        dynamic_confidence = self.calculate_dynamic_confidence(error_analysis)
        
        # Determine priority based on error severity and confidence
        priority = 'normal'
        if dynamic_confidence >= 0.85:
            priority = 'high'
        elif dynamic_confidence >= 0.75:
            priority = 'medium'
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        proposal = {
            'id': f'improvement_{timestamp}',
            'trigger': 'new_error_pattern_detected',
            'analysis': error_analysis,
            'proposed_changes': [],
            'confidence': round(dynamic_confidence, 3),  # Dynamic confidence
            'priority': priority,
            'status': 'proposed',
            'created_at': datetime.now().isoformat(),
            'auto_execute': True,
            'rollback_available': True
        }

        proposal_path = improvements_path / f'{timestamp}.json'
        with open(proposal_path, 'w') as f:
            json.dump(proposal, f, indent=2)

        print(f"💡 Improvement proposed: {proposal['id']} (confidence: {dynamic_confidence:.3f}, priority: {priority})")

        # Auto-execute immediately
        self.check_and_execute()

        return proposal

if __name__ == '__main__':
    executor = AutoImprovementExecutor()
    executed = executor.check_and_execute()
    print(f"Auto-executed {len(executed)} improvements")
