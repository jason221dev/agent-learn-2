#!/usr/bin/env python3
"""
Agent Learn 2 - Main Workflow
Autonomous Self-Improving AI Framework v2.1
Author: jason221dev
License: MIT
"""

from core.hierarchical_error_schema import HierarchicalErrorSchema, CommandHandler, GlobalOptimizations
import os

class AgentLearn2:
    """
    Main agent class for autonomous learning and improvement.
    Focus: Error handling, solution discovery, and continuous improvement.
    """
    
    def __init__(self, github_token=None):
        """Initialize the agent with error schema and global optimizations."""
        self.error_schema = HierarchicalErrorSchema()
        
        if github_token:
            self.error_schema.set_github_token(github_token)
        
        self.global_opts = self.error_schema.global_optimizations
    
    def classify_error(self, error_message: str, error_type: str = ""):
        """
        Classify an error into the hierarchical schema.
        
        Args:
            error_message: The error message to classify
            error_type: Optional explicit error type
        
        Returns:
            tuple: (category_name, group_id)
        """
        return self.error_schema.classify_error(error_message, error_type)
    
    def add_solution(self, category: str, group_id: str, 
                    solution_code: str, description: str, confidence: float):
        """
        Add a solution to an error group.
        
        Args:
            category: Error category (e.g., 'python', 'github')
            group_id: Error group ID
            solution_code: The solution code
            description: Solution description
            confidence: Confidence score (0.0-1.0)
        """
        self.error_schema.add_solution(
            category, group_id, solution_code, description, confidence
        )
    
    def get_best_solution(self, category: str, group_id: str):
        """
        Get the best ranked solution for an error group.
        
        Args:
            category: Error category
            group_id: Error group ID
        
        Returns:
            Solution object or None
        """
        return self.error_schema.get_best_solution(category, group_id)
    
    def run_discovery_cycle(self, keywords=None):
        """
        Run a discovery cycle to find new solutions.
        Currently a placeholder for future GitHub API integration.
        
        Args:
            keywords: Optional keywords to search for
        """
        print("Discovery cycle initiated")
        # Future: Implement GitHub search for new solutions
        pass
    
    def handle_command(self, command: str, context=None):
        """
        Handle a command string.
        
        Args:
            command: Command string (e.g., '/load', '/help')
            context: Optional context dictionary
        
        Returns:
            str: Command result
        """
        if context is None:
            context = {}
        
        handler = CommandHandler(self.error_schema)
        return handler.execute_command(command, context)


def main():
    """Main entry point."""
    # Initialize agent
    agent = AgentLearn2(github_token=os.getenv('GITHUB_TOKEN'))
    
    # Example: Classify an error
    category, group_id = agent.classify_error(
        "ModuleNotFoundError: No module named 'requests'"
    )
    print(f"Classified: {category}/{group_id}")
    
    # Example: Add a solution
    agent.add_solution(
        category, group_id,
        "pip install requests",
        "Install missing package",
        0.95
    )
    
    # Example: Get best solution
    best = agent.get_best_solution(category, group_id)
    if best:
        print(f"Best solution: {best.code}")
    
    # Example: Handle command
    result = agent.handle_command("/status", {})
    print(f"Status: {result}")


if __name__ == "__main__":
    main()
