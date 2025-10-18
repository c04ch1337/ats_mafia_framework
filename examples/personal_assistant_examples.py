"""
ATS MAFIA Framework Personal Assistant - Usage Examples

This module provides practical examples of using the Personal Assistant feature.
"""

import asyncio
from typing import Dict, Any

from ats_mafia_framework.config.settings import FrameworkConfig
from ats_mafia_framework.core.logging import AuditLogger
from ats_mafia_framework.voice.personal_assistant import (
    PersonalTaskType,
    PersonalPersona,
    get_personal_assistant_manager
)
from ats_mafia_framework.voice.personal_assistant_config import (
    initialize_personal_assistant_feature
)


async def example_1_book_dentist_appointment():
    """
    Example 1: Book a dentist appointment
    
    This is the most common use case - booking a routine appointment.
    """
    print("\n" + "="*60)
    print("EXAMPLE 1: Book Dentist Appointment")
    print("="*60 + "\n")
    
    # Get personal assistant manager
    pa_manager = get_personal_assistant_manager()
    
    if not pa_manager:
        print("❌ Personal Assistant Manager not initialized")
        return
    
    # Create the task
    print("Creating appointment booking task...")
    task_id = await pa_manager.create_task(
        user_id="user_example",
        task_type=PersonalTaskType.APPOINTMENT_BOOKING,
        phone_number="+1-555-DENTIST",
        intent_description="Book dental cleaning appointment for next week, morning preferred",
        context={
            "user_name": "John Doe",
            "service_type": "dental cleaning",
            "preferred_timeframe": "next week, morning",
            "patient_name": "John Doe",
            "patient_dob": "01/15/1985"
        },
        persona=PersonalPersona.PROFESSIONAL_ASSISTANT,
        requires_approval=True
    )
    
    print(f"✅ Task created: {task_id}")
    
    # Get task details
    task = pa_manager.get_task(task_id)
    if task:
        print(f"\n📝 Generated Script:")
        print("-" * 60)
        print(task.script)
        print("-" * 60)
        print(f"\nStatus: {task.status.value}")
        print(f"Requires Approval: {task.config.requires_approval}")
    
    # Approve the task
    print("\n🔍 Reviewing and approving task...")
    approved = await pa_manager.approve_task(task_id, "user_example")
    
    if approved:
        print("✅ Task approved")
        
        # Execute the task
        print("\n📞 Executing task (making call)...")
        success = await pa_manager.execute_task(task_id)
        
        if success:
            print("✅ Call completed successfully")
            
            # Get updated task with results
            task = pa_manager.get_task(task_id)
            if task and task.result:
                print(f"\n📊 Results:")
                print(f"  - Call Completed: {task.result.get('call_completed')}")
                print(f"  - Objective Achieved: {task.result.get('objective_achieved')}")
                if task.recording_file:
                    print(f"  - Recording: {task.recording_file}")
        else:
            print("❌ Call failed")
    else:
        print("❌ Failed to approve task")


async def example_2_get_store_hours():
    """
    Example 2: Get store hours (simple information inquiry)
    
    This example shows a quick information request that doesn't require approval.
    """
    print("\n" + "="*60)
    print("EXAMPLE 2: Get Store Hours (No Approval Required)")
    print("="*60 + "\n")
    
    pa_manager = get_personal_assistant_manager()
    
    if not pa_manager:
        print("❌ Personal Assistant Manager not initialized")
        return
    
    # Create task without approval requirement
    print("Creating information inquiry task...")
    task_id = await pa_manager.create_task(
        user_id="user_example",
        task_type=PersonalTaskType.INFORMATION_INQUIRY,
        phone_number="+1-555-STORE-1",
        intent_description="Find out store hours for today and tomorrow",
        context={
            "inquiry_topic": "store hours",
            "specific_questions": "What are your hours today and tomorrow?"
        },
        persona=PersonalPersona.FRIENDLY_REPRESENTATIVE,
        requires_approval=False  # Low-risk task, no approval needed
    )
    
    print(f"✅ Task created: {task_id}")
    
    # Execute immediately (no approval needed)
    print("\n📞 Executing task immediately...")
    success = await pa_manager.execute_task(task_id)
    
    if success:
        print("✅ Call completed")
        task = pa_manager.get_task(task_id)
        if task:
            print(f"\n📋 Information Obtained:")
            print(f"  Hours today: [Would be extracted from call]")
            print(f"  Hours tomorrow: [Would be extracted from call]")
    else:
        print("❌ Call failed")


async def example_3_report_service_issue():
    """
    Example 3: Report an internet service issue
    
    This shows how to handle a service problem with account information.
    """
    print("\n" + "="*60)
    print("EXAMPLE 3: Report Internet Service Issue")
    print("="*60 + "\n")
    
    pa_manager = get_personal_assistant_manager()
    
    if not pa_manager:
        print("❌ Personal Assistant Manager not initialized")
        return
    
    print("Creating service issue task...")
    task_id = await pa_manager.create_task(
        user_id="user_example",
        task_type=PersonalTaskType.SERVICE_ISSUE,
        phone_number="+1-555-ISP-HELP",
        intent_description="Report internet service outage and request technician",
        context={
            "user_name": "John Doe",
            "account_info": "Account #123456",
            "issue_description": "Internet service has been completely down for 48 hours",
            "duration_of_issue": "2 days",
            "urgency_level": "high",
            "attempted_solutions": "Restarted modem and router multiple times"
        },
        persona=PersonalPersona.PROFESSIONAL_ASSISTANT,
        requires_approval=True
    )
    
    print(f"✅ Task created: {task_id}")
    
    # Show script
    task = pa_manager.get_task(task_id)
    if task:
        print(f"\n📝 Generated Script:")
        print("-" * 60)
        print(task.script)
        print("-" * 60)
    
    # In real usage, user would review and approve
    print("\n✅ [User would review and approve via UI]")


async def example_4_social_call_rsvp():
    """
    Example 4: RSVP to an event
    
    This shows a social call scenario.
    """
    print("\n" + "="*60)
    print("EXAMPLE 4: RSVP to Event")
    print("="*60 + "\n")
    
    pa_manager = get_personal_assistant_manager()
    
    if not pa_manager:
        print("❌ Personal Assistant Manager not initialized")
        return
    
    print("Creating social call task...")
    task_id = await pa_manager.create_task(
        user_id="user_example",
        task_type=PersonalTaskType.SOCIAL_CALL,
        phone_number="+1-555-FRIEND",
        intent_description="RSVP to birthday party - confirm I'll be attending",
        context={
            "user_name": "John Doe",
            "recipient_name": "Sarah",
            "message_or_purpose": "John wanted me to RSVP for the birthday party on Saturday. He'll be there and is bringing his famous potato salad.",
            "requires_response": "Please confirm if you need him to bring anything else."
        },
        persona=PersonalPersona.FRIENDLY_REPRESENTATIVE,
        requires_approval=True
    )
    
    print(f"✅ Task created: {task_id}")


async def example_5_manage_multiple_tasks():
    """
    Example 5: Manage multiple tasks
    
    Shows how to create and track multiple tasks.
    """
    print("\n" + "="*60)
    print("EXAMPLE 5: Managing Multiple Tasks")
    print("="*60 + "\n")
    
    pa_manager = get_personal_assistant_manager()
    
    if not pa_manager:
        print("❌ Personal Assistant Manager not initialized")
        return
    
    # Create multiple tasks
    tasks = []
    
    print("Creating multiple tasks...")
    
    # Task 1: Dentist
    task1 = await pa_manager.create_task(
        user_id="user_example",
        task_type=PersonalTaskType.APPOINTMENT_BOOKING,
        phone_number="+1-555-DENTIST",
        intent_description="Book dental checkup",
        context={"service_type": "dental checkup", "preferred_timeframe": "next month"},
        persona=PersonalPersona.PROFESSIONAL_ASSISTANT
    )
    tasks.append(task1)
    print(f"  ✅ Task 1 (Dentist): {task1}")
    
    # Task 2: Auto shop
    task2 = await pa_manager.create_task(
        user_id="user_example",
        task_type=PersonalTaskType.INFORMATION_INQUIRY,
        phone_number="+1-555-AUTO-SHOP",
        intent_description="Get oil change pricing",
        context={"inquiry_topic": "oil change service", "specific_questions": "pricing and duration"},
        persona=PersonalPersona.PROFESSIONAL_ASSISTANT,
        requires_approval=False
    )
    tasks.append(task2)
    print(f"  ✅ Task 2 (Auto Shop): {task2}")
    
    # Task 3: Restaurant
    task3 = await pa_manager.create_task(
        user_id="user_example",
        task_type=PersonalTaskType.INFORMATION_INQUIRY,
        phone_number="+1-555-RESTAURANT",
        intent_description="Check hours and make reservation",
        context={"inquiry_topic": "hours and reservations"},
        persona=PersonalPersona.FRIENDLY_REPRESENTATIVE,
        requires_approval=False
    )
    tasks.append(task3)
    print(f"  ✅ Task 3 (Restaurant): {task3}")
    
    # Get active tasks
    print(f"\n📋 Active Tasks:")
    active_tasks = pa_manager.get_active_tasks("user_example")
    for task in active_tasks:
        print(f"  - {task.task_id}: {task.config.intent_description} [{task.status.value}]")
    
    # Get statistics
    print(f"\n📊 Statistics:")
    stats = pa_manager.get_statistics()
    for key, value in stats.items():
        print(f"  - {key}: {value}")


async def example_6_task_approval_workflow():
    """
    Example 6: Complete task approval workflow
    
    Shows the full workflow from creation to execution with approval.
    """
    print("\n" + "="*60)
    print("EXAMPLE 6: Complete Task Approval Workflow")
    print("="*60 + "\n")
    
    pa_manager = get_personal_assistant_manager()
    
    if not pa_manager:
        print("❌ Personal Assistant Manager not initialized")
        return
    
    # Step 1: Create task
    print("Step 1: Creating task...")
    task_id = await pa_manager.create_task(
        user_id="user_example",
        task_type=PersonalTaskType.APPOINTMENT_BOOKING,
        phone_number="+1-555-SALON",
        intent_description="Book haircut appointment",
        context={
            "user_name": "John Doe",
            "service_type": "men's haircut",
            "preferred_timeframe": "this Saturday, afternoon"
        },
        persona=PersonalPersona.PROFESSIONAL_ASSISTANT,
        requires_approval=True
    )
    print(f"  ✅ Task ID: {task_id}")
    
    # Step 2: Review task
    print("\nStep 2: Reviewing task...")
    task = pa_manager.get_task(task_id)
    if task:
        print(f"  Status: {task.status.value}")
        if task.script:
            print(f"  Script Preview:")
            print("  " + "-" * 56)
            for line in task.script.split('\n'):
                print(f"  {line}")
            print("  " + "-" * 56)
    
    # Step 3: User decides to approve
    print("\nStep 3: User approves task...")
    approved = await pa_manager.approve_task(task_id, "user_example")
    if approved:
        print("  ✅ Task approved")
        
        # Step 4: Execute task
        print("\nStep 4: Executing task...")
        success = await pa_manager.execute_task(task_id)
        
        if success:
            print("  ✅ Task executed successfully")
            
            # Step 5: Review results
            print("\nStep 5: Reviewing results...")
            task = pa_manager.get_task(task_id)
            if task:
                print(f"  Final Status: {task.status.value}")
                print(f"  Duration: {task.get_duration():.2f}s" if task.get_duration() else "  Duration: N/A")
                print(f"  Result: {task.result}")
        else:
            print("  ❌ Task execution failed")
    else:
        print("  ❌ Task approval failed")


async def example_7_cancel_task():
    """
    Example 7: Cancel a pending task
    
    Shows how to cancel a task before execution.
    """
    print("\n" + "="*60)
    print("EXAMPLE 7: Cancel Pending Task")
    print("="*60 + "\n")
    
    pa_manager = get_personal_assistant_manager()
    
    if not pa_manager:
        print("❌ Personal Assistant Manager not initialized")
        return
    
    # Create a task
    print("Creating task...")
    task_id = await pa_manager.create_task(
        user_id="user_example",
        task_type=PersonalTaskType.APPOINTMENT_BOOKING,
        phone_number="+1-555-TEST",
        intent_description="Test appointment (will be cancelled)",
        context={"service_type": "test"},
        persona=PersonalPersona.PROFESSIONAL_ASSISTANT
    )
    print(f"  ✅ Task created: {task_id}")
    
    # User changes mind and cancels
    print("\nUser decides to cancel...")
    cancelled = await pa_manager.cancel_task(task_id, reason="Changed mind, will call personally")
    
    if cancelled:
        print("  ✅ Task cancelled successfully")
    else:
        print("  ❌ Failed to cancel task")


async def example_8_view_task_history():
    """
    Example 8: View task history
    
    Shows how to retrieve completed tasks for review.
    """
    print("\n" + "="*60)
    print("EXAMPLE 8: View Task History")
    print("="*60 + "\n")
    
    pa_manager = get_personal_assistant_manager()
    
    if not pa_manager:
        print("❌ Personal Assistant Manager not initialized")
        return
    
    # Get active tasks
    print("📋 Active Tasks:")
    active_tasks = pa_manager.get_active_tasks("user_example")
    if active_tasks:
        for task in active_tasks:
            print(f"  • {task.config.intent_description}")
            print(f"    Status: {task.status.value} | Created: {task.created_at}")
    else:
        print("  No active tasks")
    
    # Get completed tasks
    print("\n✅ Completed Tasks (Last 10):")
    completed_tasks = pa_manager.get_completed_tasks("user_example", limit=10)
    if completed_tasks:
        for task in completed_tasks:
            duration = task.get_duration()
            duration_str = f"{duration:.2f}s" if duration else "N/A"
            print(f"  • {task.config.intent_description}")
            print(f"    Status: {task.status.value} | Duration: {duration_str}")
    else:
        print("  No completed tasks")
    
    # Get statistics
    print("\n📊 Overall Statistics:")
    stats = pa_manager.get_statistics()
    print(f"  Total Tasks: {stats['total_tasks']}")
    print(f"  Completed: {stats['completed_tasks']}")
    print(f"  Failed: {stats['failed_tasks']}")
    print(f"  Success Rate: {stats['success_rate']:.1%}")


async def example_9_custom_task_with_full_context():
    """
    Example 9: Custom task with comprehensive context
    
    Shows how to provide detailed context for complex tasks.
    """
    print("\n" + "="*60)
    print("EXAMPLE 9: Custom Task with Full Context")
    print("="*60 + "\n")
    
    pa_manager = get_personal_assistant_manager()
    
    if not pa_manager:
        print("❌ Personal Assistant Manager not initialized")
        return
    
    print("Creating custom task with detailed context...")
    task_id = await pa_manager.create_task(
        user_id="user_example",
        task_type=PersonalTaskType.CUSTOM,
        phone_number="+1-555-SUPPORT",
        intent_description="Follow up on support ticket and request status update",
        context={
            "user_name": "John Doe",
            "account_number": "ACCT-123456",
            "ticket_number": "TICKET-789",
            "issue_description": "Billing discrepancy from last month",
            "amount_disputed": "$75.00",
            "previous_contact_date": "October 10, 2025",
            "requested_resolution": "Credit to account or explanation of charge",
            "urgency_level": "medium",
            "best_contact_time": "business hours",
            "preferred_contact_method": "email"
        },
        persona=PersonalPersona.PROFESSIONAL_ASSISTANT,
        requires_approval=True
    )
    
    print(f"✅ Task created with comprehensive context: {task_id}")
    
    task = pa_manager.get_task(task_id)
    if task:
        print(f"\n📝 Script will incorporate all context:")
        print(f"  - Account: {task.config.context.get('account_number')}")
        print(f"  - Ticket: {task.config.context.get('ticket_number')}")
        print(f"  - Issue: {task.config.context.get('issue_description')}")
        print(f"  - Amount: {task.config.context.get('amount_disputed')}")


async def run_all_examples():
    """Run all examples in sequence."""
    print("\n" + "="*60)
    print("PERSONAL ASSISTANT FEATURE - USAGE EXAMPLES")
    print("="*60)
    
    # Note: In real usage, Personal Assistant Manager must be initialized first
    # This would typically be done during framework initialization
    
    print("\n⚠️  Note: These examples assume Personal Assistant Manager is initialized")
    print("⚠️  In production, initialize with:")
    print("    from ats_mafia_framework.voice.personal_assistant_config import initialize_personal_assistant_feature")
    print("    initialize_personal_assistant_feature(config, audit_logger)")
    
    # Run examples
    await example_1_book_dentist_appointment()
    await asyncio.sleep(1)
    
    await example_2_get_store_hours()
    await asyncio.sleep(1)
    
    await example_3_report_service_issue()
    await asyncio.sleep(1)
    
    await example_4_social_call_rsvp()
    await asyncio.sleep(1)
    
    await example_5_manage_multiple_tasks()
    await asyncio.sleep(1)
    
    await example_6_task_approval_workflow()
    await asyncio.sleep(1)
    
    await example_7_cancel_task()
    await asyncio.sleep(1)
    
    await example_8_view_task_history()
    await asyncio.sleep(1)
    
    await example_9_custom_task_with_full_context()
    
    print("\n" + "="*60)
    print("ALL EXAMPLES COMPLETE")
    print("="*60 + "\n")


# Quick start example
async def quick_start_example():
    """
    Quick start example - minimal code to get started.
    
    Perfect for copy-paste to get up and running quickly.
    """
    print("\n" + "="*60)
    print("QUICK START EXAMPLE")
    print("="*60 + "\n")
    
    # Initialize (done once during app startup)
    config = FrameworkConfig()
    config.set('voice.personal_assistant.enabled', True)
    config.set('voice.personal_assistant.phone_provider', 'mock')
    
    initialized = initialize_personal_assistant_feature(config)
    
    if not initialized:
        print("❌ Failed to initialize")
        return
    
    print("✅ Personal Assistant initialized\n")
    
    # Get manager
    pa_manager = get_personal_assistant_manager()
    assert pa_manager is not None
    
    # Create and execute a simple task
    print("Creating simple task...")
    task_id = await pa_manager.create_task(
        user_id="quickstart_user",
        task_type=PersonalTaskType.INFORMATION_INQUIRY,
        phone_number="+1-555-1234",
        intent_description="Check store hours",
        context={"inquiry_topic": "store hours"},
        persona=PersonalPersona.FRIENDLY_REPRESENTATIVE,
        requires_approval=False
    )
    
    print(f"✅ Task created: {task_id}")
    print(f"\n📞 Executing...")
    
    success = await pa_manager.execute_task(task_id)
    print(f"{'✅ Success!' if success else '❌ Failed'}")


if __name__ == "__main__":
    # Run quick start example
    print("Running Quick Start Example...")
    asyncio.run(quick_start_example())
    
    # Uncomment to run all examples
    # asyncio.run(run_all_examples())