import re


def get_triggers():
    # Matches commands starting with 'orchestrate', 'plan and execute', or 'run plan'
    return [
        r"^orchestrate (.+)",
        r"^plan and execute (.+)",
        r"^run plan (.+)"
    ]

def execute(jarvis_instance, text, original_text, match=None):
    from agent_module import OrchestratorAgent
    query = match.group(1).strip()
    jarvis_instance._respond("Initializing supervisor orchestrator core, please hold...")
    
    # Instantiate Orchestrator
    orchestrator = OrchestratorAgent()
    
    # Step 1: Decompose request
    plan = orchestrator.decompose_request(query)
    if not plan or "tasks" not in plan:
        jarvis_instance._respond("Sir, I was unable to break this down into a structured task plan.")
        return False
        
    # Step 2: Show task execution details
    task_count = len(plan["tasks"])
    jarvis_instance._respond(f"Plan compiled successfully with {task_count} sub-tasks. Spawning workers...")
    
    # Step 3: Run execution
    summary = orchestrator.execute_plan(plan, jarvis_instance)
    
    # Step 4: Respond with consolidated summary
    jarvis_instance._respond(summary)
    return False
