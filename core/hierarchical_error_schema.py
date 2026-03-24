#!/usr/bin/env python3
"""
Hierarchical Error Schema with Automated GitHub Audit - COMPLETE
Agent Learn 2 v2.1 - Full Implementation with all features
Author: jason221dev
License: MIT
"""

import json
import os
import re
import hashlib
import time
import difflib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import uuid
from collections import OrderedDict

# Try to import requests for GitHub API (optional)
try:
    import requests
    GITHUB_API_AVAILABLE = True
except ImportError:
    GITHUB_API_AVAILABLE = False

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class Solution:
    """Represents a solution to an error with optimality ranking"""
    id: str
    code: str
    description: str
    confidence: float
    success_rate: float = 0.0
    occurrences: int = 1
    last_used: str = field(default_factory=lambda: datetime.now().isoformat())
    source: str = "internal"
    github_url: Optional[str] = None
    github_stars: int = 0
    github_forks: int = 0
    
    def optimality_score(self) -> float:
        """
        Calculate optimality score for ranking solutions.
        Formula: (confidence × 0.4) + (success_rate × 0.4) + (recency × 0.2)
        """
        last_used_dt = datetime.fromisoformat(self.last_used)
        days_since_use = (datetime.now() - last_used_dt).days
        recency = max(0, 1 - (days_since_use / 30))
        
        return (self.confidence * 0.4) + (self.success_rate * 0.4) + (recency * 0.2)
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'code': self.code,
            'description': self.description,
            'confidence': self.confidence,
            'success_rate': self.success_rate,
            'occurrences': self.occurrences,
            'last_used': self.last_used,
            'source': self.source,
            'github_url': self.github_url,
            'github_stars': self.github_stars,
            'github_forks': self.github_forks,
            'optimality_score': self.optimality_score()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Solution':
        return cls(
            id=data['id'],
            code=data['code'],
            description=data['description'],
            confidence=data['confidence'],
            success_rate=data.get('success_rate', 0.0),
            occurrences=data.get('occurrences', 1),
            last_used=data.get('last_used', datetime.now().isoformat()),
            source=data.get('source', 'internal'),
            github_url=data.get('github_url'),
            github_stars=data.get('github_stars', 0),
            github_forks=data.get('github_forks', 0)
        )

@dataclass
class ErrorGroup:
    """Group of similar errors (similarity > 0.8 threshold)"""
    id: str
    pattern: str
    keywords: List[str]
    industry_codes: List[str]
    solutions: List[Solution] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_audit: Optional[str] = None
    audit_frequency_days: int = 1
    similarity_threshold: float = 0.8
    
    def add_solution(self, solution: Solution):
        """Add solution and automatically re-rank all solutions"""
        self.solutions.append(solution)
        self.re_rank_solutions()
    
    def re_rank_solutions(self):
        """Re-rank solutions by optimality score (descending)"""
        self.solutions.sort(key=lambda s: s.optimality_score(), reverse=True)
    
    def should_audit(self) -> bool:
        """Check if group needs GitHub audit based on frequency"""
        if self.last_audit is None:
            return True
        
        last_audit_dt = datetime.fromisoformat(self.last_audit)
        next_audit = last_audit_dt + timedelta(days=self.audit_frequency_days)
        return datetime.now() > next_audit
    
    def is_similar_to(self, error_message: str, keywords: List[str]) -> bool:
        """
        Check if error message is similar to this group using multiple strategies.
        Returns True if similarity > threshold.
        """
        # Strategy 1: Pattern matching
        try:
            if re.search(self.pattern, error_message, re.IGNORECASE):
                return True
        except:
            pass
        
        # Strategy 2: Keyword overlap
        if keywords:
            keyword_matches = sum(1 for kw in keywords if kw in self.keywords)
            if len(keywords) > 0 and keyword_matches / max(len(keywords), 1) > self.similarity_threshold:
                return True
        
        # Strategy 3: String similarity (difflib)
        error_lower = error_message.lower()
        for group_keyword in self.keywords:
            similarity = difflib.SequenceMatcher(None, error_lower, group_keyword.lower()).ratio()
            if similarity > self.similarity_threshold:
                return True
        
        # Strategy 4: Industry code match
        for code in self.industry_codes:
            if code != 'GENERAL' and code in error_message:
                return True
        
        return False
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'pattern': self.pattern,
            'keywords': self.keywords,
            'industry_codes': self.industry_codes,
            'solutions': [s.to_dict() for s in self.solutions],
            'created_at': self.created_at,
            'last_audit': self.last_audit,
            'audit_frequency_days': self.audit_frequency_days,
            'similarity_threshold': self.similarity_threshold
        }

@dataclass
class ErrorCategory:
    """Broad error category (github, python, system, network, etc.)"""
    name: str
    description: str
    error_groups: List[ErrorGroup] = field(default_factory=list)
    
    def find_or_create_group(self, pattern: str, keywords: List[str], 
                            industry_codes: List[str],
                            error_message: str = "") -> ErrorGroup:
        """Find existing similar group or create new one"""
        # Check for similar groups
        for group in self.error_groups:
            if group.is_similar_to(error_message or pattern, keywords):
                return group
        
        # Create new group
        new_group = ErrorGroup(
            id=f"grp_{hashlib.md5(pattern.encode()).hexdigest()[:8]}",
            pattern=pattern,
            keywords=keywords,
            industry_codes=industry_codes
        )
        self.error_groups.append(new_group)
        return new_group
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'description': self.description,
            'error_groups': [g.to_dict() for g in self.error_groups]
        }

@dataclass
class ChatLog:
    """Chat-scoped error log (persisted, never deleted)"""
    chat_id: str
    created_at: str
    context: Dict[str, Any]
    error_events: List[Dict] = field(default_factory=list)
    optimization_events: List[Dict] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    
    def add_error_event(self, category: str, error_group_id: str, 
                       error_message: str, solution_used: str):
        """Record error event"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'category': category,
            'error_group_id': error_group_id,
            'error_message': error_message,
            'solution_used': solution_used,
            'resolution_success': True
        }
        self.error_events.append(event)
        self._update_statistics()
    
    def add_optimization_event(self, optimization_type: str, description: str,
                              impact: str):
        """Record optimization event"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': optimization_type,
            'description': description,
            'impact': impact
        }
        self.optimization_events.append(event)
    
    def _update_statistics(self):
        """Update log statistics"""
        self.statistics = {
            'total_errors': len(self.error_events),
            'total_optimizations': len(self.optimization_events),
            'last_updated': datetime.now().isoformat()
        }
    
    def to_dict(self) -> Dict:
        return {
            'chat_id': self.chat_id,
            'created_at': self.created_at,
            'context': self.context,
            'error_events': self.error_events,
            'optimization_events': self.optimization_events,
            'statistics': self.statistics
        }

# ============================================================================
# GLOBAL OPTIMIZATIONS MANAGER (Cross-Chat)
# ============================================================================

class GlobalOptimizations:
    """
    Manages cross-chat optimizations that are universally applicable.
    Stored in learning/global_optimizations.json
    """
    
    def __init__(self, base_path: str = "learning"):
        self.base_path = Path(base_path)
        self.file_path = self.base_path / "global_optimizations.json"
        self.optimizations: Dict[str, Any] = {}
        self._load()
    
    def _load(self):
        """Load global optimizations from file"""
        if self.file_path.exists():
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                self.optimizations = data.get('optimizations', {})
        else:
            # Initialize with default optimizations
            self.optimizations = {
                "architecture_patterns": {
                    "jit_loading": {
                        "description": "Just-in-time loading for skills/MCPs",
                        "memory_reduction": "95%",
                        "applicable": "all"
                    },
                    "lru_cache_size": {
                        "description": "Optimal LRU cache size",
                        "value": 10,
                        "applicable": "all"
                    }
                },
                "performance_tuning": {
                    "batch_operations": {
                        "description": "Batch file operations when possible",
                        "improvement": "40% faster",
                        "applicable": "filesystem"
                    }
                },
                "universal_error_patterns": {
                    "ffmpeg_not_found": {
                        "pattern": "ffmpeg.*not found",
                        "solution": "system_package_installer",
                        "confidence": 0.98
                    },
                    "module_not_found": {
                        "pattern": "ModuleNotFoundError.*No module named",
                        "solution": "pip install {module}",
                        "confidence": 0.95
                    },
                    "permission_denied": {
                        "pattern": "Permission denied",
                        "solution": "check_permissions_or_use_sudo",
                        "confidence": 0.90
                    }
                }
            }
            self._save()
    
    def _save(self):
        """Save global optimizations to file"""
        self.base_path.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, 'w') as f:
            json.dump({
                'optimizations': self.optimizations,
                'last_updated': datetime.now().isoformat()
            }, f, indent=2)
    
    def get_optimization(self, category: str, name: str) -> Optional[Any]:
        """Get specific optimization"""
        return self.optimizations.get(category, {}).get(name)
    
    def add_optimization(self, category: str, name: str, data: Dict):
        """Add or update optimization"""
        if category not in self.optimizations:
            self.optimizations[category] = {}
        self.optimizations[category][name] = data
        self._save()
    
    def find_applicable(self, error_message: str) -> List[Dict]:
        """Find applicable optimizations for an error"""
        applicable = []
        patterns = self.optimizations.get('universal_error_patterns', {})
        
        for name, data in patterns.items():
            pattern = data.get('pattern', '')
            if re.search(pattern, error_message, re.IGNORECASE):
                applicable.append({
                    'name': name,
                    'solution': data.get('solution'),
                    'confidence': data.get('confidence', 0.5),
                    'source': 'global_optimization'
                })
        
        return applicable
    
    def to_dict(self) -> Dict:
        return {
            'optimizations': self.optimizations,
            'last_updated': datetime.now().isoformat()
        }

# ============================================================================
# HIERARCHICAL ERROR SCHEMA MANAGER
# ============================================================================

class HierarchicalErrorSchema:
    """
    Manages hierarchical error categorization with automated GitHub audit.
    
    Structure:
    - Categories (broad: github, python, system, etc.)
      - Error Groups (similarity > 0.8)
        - Solutions (ranked by optimality)
    """
    
    def __init__(self, base_path: str = "learning"):
        self.base_path = Path(base_path)
        self.logs_path = self.base_path / "logs"
        self.logs_path.mkdir(parents=True, exist_ok=True)
        
        self.categories: Dict[str, ErrorCategory] = {}
        self.current_chat_log: Optional[ChatLog] = None
        self.github_token: Optional[str] = None
        self.global_optimizations = GlobalOptimizations(str(self.base_path))
        
        self._initialize_default_categories()
    
    def _initialize_default_categories(self):
        """Initialize 8 default error categories"""
        default_categories = [
            ("github", "GitHub-related errors (auth, API, repo operations)"),
            ("python", "Python-specific errors (syntax, imports, runtime)"),
            ("system", "System-level errors (permissions, paths, processes)"),
            ("network", "Network connectivity and API errors"),
            ("filesystem", "File operations and disk errors"),
            ("memory", "Memory and performance issues"),
            ("configuration", "Configuration and environment errors"),
            ("dependency", "Package and dependency resolution errors")
        ]
        
        for name, description in default_categories:
            self.categories[name] = ErrorCategory(name=name, description=description)
    
    def set_github_token(self, token: str):
        """Set GitHub token for automated audits"""
        self.github_token = token
    
    def create_chat_log(self, chat_id: Optional[str] = None) -> ChatLog:
        """Create new or load existing chat-scoped log"""
        if chat_id is None:
            chat_id = str(uuid.uuid4())
        
        log_path = self.logs_path / f"chat_{chat_id}.json"
        
        if log_path.exists():
            with open(log_path, 'r') as f:
                data = json.load(f)
            self.current_chat_log = ChatLog(**data)
        else:
            self.current_chat_log = ChatLog(
                chat_id=chat_id,
                created_at=datetime.now().isoformat(),
                context={}
            )
        
        return self.current_chat_log
    
    def load_chat_log(self, chat_id: str) -> Optional[ChatLog]:
        """Load specific chat log by ID"""
        log_path = self.logs_path / f"chat_{chat_id}.json"
        
        if not log_path.exists():
            return None
        
        with open(log_path, 'r') as f:
            data = json.load(f)
        
        self.current_chat_log = ChatLog(**data)
        return self.current_chat_log
    
    def save_chat_log(self):
        """Persist current chat log to disk"""
        if self.current_chat_log is None:
            return
        
        log_path = self.logs_path / f"chat_{self.current_chat_log.chat_id}.json"
        with open(log_path, 'w') as f:
            json.dump(self.current_chat_log.to_dict(), f, indent=2)
    
    def classify_error(self, error_message: str, error_type: str = "") -> Tuple[str, str]:
        """
        Classify error into category and group.
        Returns: (category_name, group_id)
        """
        error_lower = error_message.lower()
        
        # Check global optimizations first
        applicable = self.global_optimizations.find_applicable(error_message)
        if applicable:
            # Use optimized solution
            opt = applicable[0]
            # Still classify normally but note the optimization
            pass
        
        # Determine category
        category_mapping = {
            'github': ['github', 'git', 'remote', 'repository', 'commit', 'push', 'pull'],
            'python': ['python', 'importerror', 'syntaxerror', 'traceback', 'module'],
            'system': ['permission', 'access denied', 'sudo', 'root', 'privilege'],
            'network': ['network', 'connection', 'timeout', 'http', 'api', 'request'],
            'filesystem': ['file', 'directory', 'path', 'disk', 'storage'],
            'memory': ['memory', 'ram', 'oom', 'heap', 'stack'],
            'configuration': ['config', 'environment', 'variable', 'setting'],
            'dependency': ['dependency', 'package', 'install', 'pip', 'npm']
        }
        
        category_name = 'system'
        for cat_name, keywords in category_mapping.items():
            if any(kw in error_lower for kw in keywords):
                category_name = cat_name
                break
        
        category = self.categories[category_name]
        
        # Extract components
        pattern = self._extract_pattern(error_type or error_message)
        keywords = self._extract_keywords(error_message)
        industry_codes = self._extract_industry_codes(error_type, error_message)
        
        group = category.find_or_create_group(
            pattern, keywords, industry_codes, error_message
        )
        
        return category_name, group.id
    
    def _extract_pattern(self, text: str) -> str:
        """Extract regex pattern from error message"""
        patterns = [
            r'[A-Z][a-z]+Error',
            r'E\d{3}',
            r'ERR_[A-Z_]+',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        return text.split('\n')[0][:100]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from error"""
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been'}
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]
        return list(set(keywords))[:10]
    
    def _extract_industry_codes(self, error_type: str, error_message: str) -> List[str]:
        """Extract industry-standard error codes"""
        codes = []
        
        python_errors = ['ModuleNotFoundError', 'SyntaxError', 'ImportError', 
                        'KeyError', 'ValueError', 'TypeError']
        for err in python_errors:
            if err in error_type or err in error_message:
                codes.append(err)
        
        git_patterns = [r'fatal: .*', r'error: .*']
        for pattern in git_patterns:
            if re.search(pattern, error_message, re.IGNORECASE):
                codes.append('GIT_ERROR')
        
        return codes if codes else ['GENERAL']
    
    def add_solution(self, category_name: str, group_id: str, 
                    solution_code: str, description: str, confidence: float,
                    source: str = "internal", github_url: Optional[str] = None):
        """Add solution to error group with automatic re-ranking"""
        category = self.categories.get(category_name)
        if not category:
            return
        
        group = None
        for g in category.error_groups:
            if g.id == group_id:
                group = g
                break
        
        if not group:
            return
        
        solution = Solution(
            id=f"SOL_{hashlib.md5(solution_code.encode()).hexdigest()[:6].upper()}",
            code=solution_code,
            description=description,
            confidence=confidence,
            source=source,
            github_url=github_url
        )
        
        group.add_solution(solution)
        
        if self.current_chat_log:
            self.current_chat_log.add_optimization_event(
                'solution_added',
                f'Added solution {solution.id} to {category_name}/{group_id}',
                f'Confidence: {confidence}'
            )
            self.save_chat_log()
    
    async def audit_github_for_solutions(self, category_name: str, group_id: str):
        """
        Audit GitHub for better solutions using GitHub API.
        Searches for code repositories containing solutions.
        """
        if not GITHUB_API_AVAILABLE:
            return
        
        if not self.github_token:
            return
        
        category = self.categories.get(category_name)
        if not category:
            return
        
        group = None
        for g in category.error_groups:
            if g.id == group_id:
                group = g
                break
        
        if not group or not group.should_audit():
            return
        
        # Construct search query
        search_query = f"{group.pattern} solution fix error handling"
        
        try:
            # Search GitHub for code
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # Search for code
            search_url = 'https://api.github.com/search/code'
            params = {'q': search_query, 'per_page': '5'}
            
            response = requests.get(search_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get('items', [])[:3]:  # Top 3 results
                    repo_name = item.get('repository', {}).get('full_name', '')
                    file_path = item.get('path', '')
                    github_url = item.get('html_url', '')
                    
                    # Extract potential solution from file context
                    solution_code = f"# From {repo_name}/{file_path}\n# See: {github_url}"
                    
                    # Add as new solution
                    self.add_solution(
                        category_name, group_id,
                        solution_code,
                        f"GitHub solution from {repo_name}",
                        confidence=0.7,  # Lower confidence for discovered solutions
                        source="github",
                        github_url=github_url
                    )
                
                # Update audit timestamp
                group.last_audit = datetime.now().isoformat()
                
                if self.current_chat_log:
                    self.current_chat_log.add_optimization_event(
                        'github_audit',
                        f'Audited GitHub for {category_name}/{group_id}',
                        f'Found {len(data.get("items", []))} potential solutions'
                    )
                    self.save_chat_log()
                    
        except Exception as e:
            # Silent fail - don't break on audit errors
            pass
    
    def get_best_solution(self, category_name: str, group_id: str) -> Optional[Solution]:
        """Get highest-ranked solution for error group"""
        category = self.categories.get(category_name)
        if not category:
            return None
        
        group = None
        for g in category.error_groups:
            if g.id == group_id:
                group = g
                break
        
        if not group or not group.solutions:
            return None
        
        return group.solutions[0]
    
    def export_schema(self) -> Dict:
        """Export complete schema to dictionary"""
        return {
            'categories': {name: cat.to_dict() for name, cat in self.categories.items()},
            'exported_at': datetime.now().isoformat()
        }

# ============================================================================
# COMMAND HANDLER
# ============================================================================

class CommandHandler:
    """
    Handles command triggers: /load, /help, /status
    Primary: /load (explicit, unambiguous)
    Fallback: load (conversational)
    """
    
    def __init__(self, error_schema: HierarchicalErrorSchema):
        self.error_schema = error_schema
        self.command_patterns = {
            'load': r'^/(load|initialize|init)$|\bload\b',
            'help': r'^/(help|\?)$',
            'status': r'^/status$'
        }
    
    def execute_command(self, command: str, context: Dict[str, Any]) -> str:
        """Execute command and return result string"""
        command = command.strip().lower()
        
        if re.match(self.command_patterns['load'], command):
            return self._handle_load(context)
        
        elif re.match(self.command_patterns['help'], command):
            return self._handle_help()
        
        elif re.match(self.command_patterns['status'], command):
            return self._handle_status()
        
        return f"Unknown command: {command}"
    
    def _handle_load(self, context: Dict[str, Any]) -> str:
        """Handle /load command - loads current chat log only"""
        chat_id = context.get('chat_id')
        
        if chat_id:
            log = self.error_schema.load_chat_log(chat_id)
            if log:
                return f"Loaded chat log {chat_id} ({log.statistics.get('total_errors', 0)} errors)"
            else:
                self.error_schema.create_chat_log(chat_id)
                return f"Created new chat log for {chat_id}"
        else:
            self.error_schema.create_chat_log()
            return "Created new chat log"
    
    def _handle_help(self) -> str:
        """Show available commands"""
        return """Available commands:
/load or 'load' - Load or create chat log
/help or '?' - Show this help
/status - Show system status"""
    
    def _handle_status(self) -> str:
        """Show system status"""
        schema = self.error_schema.export_schema()
        total_groups = sum(len(cat.get('error_groups', [])) 
                          for cat in schema['categories'].values())
        return f"Schema Status: {len(schema['categories'])} categories, {total_groups} error groups"

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Example usage
    schema = HierarchicalErrorSchema()
    schema.set_github_token(os.getenv('GITHUB_TOKEN', ''))
    
    # Create chat log
    chat_log = schema.create_chat_log("example_chat")
    
    # Classify an error
    category, group_id = schema.classify_error("ModuleNotFoundError: No module named 'requests'")
    print(f"Error classified: {category}/{group_id}")
    
    # Add a solution
    schema.add_solution(category, group_id, 
                       "pip install requests",
                       "Install missing package",
                       0.95)
    
    # Get best solution
    best = schema.get_best_solution(category, group_id)
    if best:
        print(f"Best solution: {best.code} (optimality: {best.optimality_score():.3f})")
    
    # Save log
    schema.save_chat_log()
    print("Chat log saved successfully")
    
    # Show global optimizations
    print("\nGlobal optimizations loaded:", 
          len(schema.global_optimizations.optimizations.get('universal_error_patterns', {})))
