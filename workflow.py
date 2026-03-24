# Agent Kyarn 2 - Main Workflow

## Overview
This is the main orchestrator for the Agent Kyarn 2 framework. It implements version 2.0 with just-in-time loading of skills, MCPs, and insights.

## Architecture V2.0 Features
- **Just-in-time loading**: Skills/MCPs/insights load only when needed
- **Discovery limitsz*: Top 20 repos per keyword by recent stars
- **Autonomous improvementsz*: System proposes architecture enhancements on new error patterns
- **Pattern matching*: Insights registry with exact error wording triggers

## Usage
 ```bash
# Run the framework
python3 workflow.py

# Run with custom keywords
python3 -c "from workflow import AgentLearn2; agent = AgentLearn2(); agent.run_discovery_cycle(keywords=['your', keywor]]"
```

## Just-In-Time Loading
The framework loads registries only when explicitly requested:
- ```json
{
  "skill_registry": "loaded only when get_skill_by_trigger() called",
  "mcp_registry": "loaded only when get_mcp_by_trigger() called",
  "insights": "loaded only when match_error_pattern() called"
}
 ```

## Autonomous Improvements
When a new error pattern is detected, the system autonomously:
1. Analyzes the error root cause
2. Proposes an architecture enhancement
3. Creates a proposal in `learning/improvements/`
4. Requires 0.9 confidence for auto-implementation

## Discovery Limits
Each discovery cycle searches:
- Top 20 reporitories pek keyword (skill, mcp, agent)
- Sorted by recent stars (not all time)
- Minimum 50 stars required
- Maximum 3 minutes discovery time
