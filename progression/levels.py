"""
Level and title system for agent progression.
Defines milestones and promotion logic.
"""
# Level milestones
LEVEL_SENIOR_WORKER = 10        # Level 10: Senior Worker (1000 XP)
LEVEL_TEAM_LEADER = 20          # Level 20: Team Leader (5000 XP)
LEVEL_DEPUTY_SUPERVISOR = 30    # Level 30: Deputy Supervisor (15000 XP)
LEVEL_SUPERVISOR_ELIGIBLE = 40  # Level 40: Supervisor-eligible (30000 XP)
LEVEL_MILESTONES = {
    10: "Senior Worker",
    20: "Team Leader",
    30: "Deputy Supervisor",
    40: "Supervisor-Eligible"
}
def get_title_for_level(level: int) -> str:
    """Get the title for a given level."""
    if level >= LEVEL_SUPERVISOR_ELIGIBLE:
        return "Supervisor-Eligible"
    elif level >= LEVEL_DEPUTY_SUPERVISOR:
        return "Deputy Supervisor"
    elif level >= LEVEL_TEAM_LEADER:
        return "Team Leader"
    elif level >= LEVEL_SENIOR_WORKER:
        return "Senior Worker"
    else:
        return "Worker"