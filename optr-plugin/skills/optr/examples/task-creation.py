#!/usr/bin/env python3
"""
Example script for parsing PLAN.md and creating tasks.

This demonstrates how to convert plan items into TaskCreate calls.
Not meant to be executed directly - use Claude's TaskCreate tool instead.
"""

def parse_plan_to_tasks(plan_content):
    """
    Parse PLAN.md content and extract task items.

    Args:
        plan_content: Raw text content of PLAN.md

    Returns:
        List of task dictionaries with subject, description, activeForm
    """
    tasks = []
    lines = plan_content.split('\n')
    current_section = None

    for line in lines:
        line = line.strip()

        # Track section for context
        if line.startswith('##'):
            current_section = line.replace('##', '').strip()

        # Extract task items (marked with -)
        if line.startswith('- [ ]') or line.startswith('-'):
            # Extract task description
            task_text = line.replace('- [ ]', '').replace('-', '').strip()

            # Clean up task text
            if task_text:
                # Create active form (present continuous)
                # "Implement feature" -> "Implementing feature"
                active_form = task_text
                if active_form.startswith('Add'):
                    active_form = 'Adding ' + active_form[3:].lstrip()
                elif active_form.startswith('Implement'):
                    active_form = 'Implementing ' + active_form[9:].lstrip()
                elif active_form.startswith('Create'):
                    active_form = 'Creating ' + active_form[6:].lstrip()
                elif active_form.startswith('Fix'):
                    active_form = 'Fixing ' + active_form[3:].lstrip()
                elif active_form.startswith('Build'):
                    active_form = 'Building ' + active_form[5:].lstrip()

                # Build subject (imperative form)
                subject = task_text

                # Build description with context
                description = f"Task from {current_section}: {task_text}"

                tasks.append({
                    'subject': subject,
                    'description': description,
                    'activeForm': active_form
                })

    return tasks


# Example usage with Claude:
#
# 1. Read PLAN.md using Read tool
# 2. Parse tasks manually or with assistance
# 3. For each task, use TaskCreate:
#    TaskCreate(
#        subject="Implement user authentication",
#        description="Create JWT-based auth system...",
#        activeForm="Implementing user authentication"
#    )

if __name__ == '__main__':
    # Example PLAN.md content
    example_plan = """
    # Project: Todo App

    ## Backend
    - Set up Express server with TypeScript
    - Create user authentication endpoints
    - Implement CRUD operations for todos

    ## Frontend
    - Initialize React project with Vite
    - Build todo list component
    - Add form for creating todos
    """

    tasks = parse_plan_to_tasks(example_plan)

    print("Parsed tasks:")
    for i, task in enumerate(tasks, 1):
        print(f"\n{i}. Subject: {task['subject']}")
        print(f"   Active Form: {task['activeForm']}")
        print(f"   Description: {task['description']}")
