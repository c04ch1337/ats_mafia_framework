"""
ATS MAFIA Framework LLM CLI Commands

This module provides command-line interface commands for LLM model
management, cost tracking, and budget control.
"""

import click
import json
from typing import Optional
from tabulate import tabulate

from ..core.llm_models import ModelRegistry, ModelSelector, ModelTier, ModelCapability
from ..core.cost_tracker import CostTracker


@click.group(name='llm')
def llm_cli():
    """LLM model management and cost tracking commands."""
    pass


@llm_cli.command(name='list-models')
@click.option('--provider', '-p', help='Filter by provider')
@click.option('--tier', '-t', type=click.Choice(['ENTRY', 'STANDARD', 'ADVANCED', 'PREMIUM']), help='Filter by tier')
@click.option('--task', help='Filter by task recommendation')
@click.option('--max-cost', type=float, help='Maximum cost per 1k tokens')
@click.option('--json-output', is_flag=True, help='Output as JSON')
def list_models(provider: Optional[str], tier: Optional[str], task: Optional[str], 
                max_cost: Optional[float], json_output: bool):
    """List available LLM models."""
    try:
        registry = ModelRegistry()
        
        # Apply filters
        tier_enum = ModelTier(tier.upper()) if tier else None
        models = registry.list_models(
            provider=provider,
            tier=tier_enum,
            max_cost_per_1k=max_cost
        )
        
        # Filter by task if specified
        if task:
            models = [m for m in models if task in m.recommended_for]
        
        if json_output:
            output = [m.to_dict() for m in models]
            click.echo(json.dumps(output, indent=2))
        else:
            # Table output
            if not models:
                click.echo("No models found matching criteria.")
                return
            
            table_data = []
            for model in models:
                table_data.append([
                    model.get_full_name(),
                    model.tier.value,
                    f"${model.cost_per_1k_input_tokens:.4f}",
                    f"${model.cost_per_1k_output_tokens:.4f}",
                    f"{model.context_window:,}",
                    f"{model.reasoning_score:.2f}",
                    f"{model.speed_score:.2f}"
                ])
            
            headers = ['Model', 'Tier', 'Input Cost/1K', 'Output Cost/1K', 'Context', 'Reasoning', 'Speed']
            click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))
            click.echo(f"\nTotal: {len(models)} models")
    
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()


@llm_cli.command(name='show-model')
@click.argument('provider')
@click.argument('model_name')
def show_model(provider: str, model_name: str):
    """Show detailed information about a specific model."""
    try:
        registry = ModelRegistry()
        model = registry.get_model(provider, model_name)
        
        if not model:
            click.echo(f"Model not found: {provider}/{model_name}", err=True)
            raise click.Abort()
        
        # Display model information
        click.echo(f"\n{'='*60}")
        click.echo(f"Model: {model.display_name}")
        click.echo(f"Provider: {model.provider}")
        click.echo(f"{'='*60}\n")
        
        click.echo(f"Tier: {model.tier.value}")
        click.echo(f"Context Window: {model.context_window:,} tokens")
        click.echo(f"\nCosts:")
        click.echo(f"  Input:  ${model.cost_per_1k_input_tokens:.4f} per 1K tokens")
        click.echo(f"  Output: ${model.cost_per_1k_output_tokens:.4f} per 1K tokens")
        
        click.echo(f"\nPerformance:")
        click.echo(f"  Reasoning Score: {model.reasoning_score:.2f}/1.0")
        click.echo(f"  Speed Score: {model.speed_score:.2f}/1.0")
        
        click.echo(f"\nCapabilities:")
        for cap in model.capabilities:
            click.echo(f"  - {cap.value}")
        
        if model.recommended_for:
            click.echo(f"\nRecommended For:")
            for task in model.recommended_for:
                click.echo(f"  - {task}")
        
        if model.max_requests_per_minute:
            click.echo(f"\nRate Limit: {model.max_requests_per_minute} requests/minute")
        
        click.echo()
    
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()


@llm_cli.command(name='recommend')
@click.argument('task_type')
@click.option('--tier', type=click.Choice(['ENTRY', 'STANDARD', 'ADVANCED', 'PREMIUM']), help='Preferred tier')
@click.option('--max-cost', type=float, help='Maximum cost per request (estimated)')
@click.option('--limit', '-n', type=int, default=5, help='Number of recommendations')
def recommend_models(task_type: str, tier: Optional[str], max_cost: Optional[float], limit: int):
    """Get model recommendations for a specific task type."""
    try:
        registry = ModelRegistry()
        
        tier_enum = ModelTier(tier.upper()) if tier else None
        recommendations = registry.get_recommended_models(
            task_type=task_type,
            tier=tier_enum,
            max_cost_per_request=max_cost
        )
        
        if not recommendations:
            click.echo(f"No recommendations found for task: {task_type}")
            return
        
        # Limit results
        recommendations = recommendations[:limit]
        
        click.echo(f"\nTop {len(recommendations)} recommendations for '{task_type}':\n")
        
        for i, model in enumerate(recommendations, 1):
            click.echo(f"{i}. {model.display_name} ({model.get_full_name()})")
            click.echo(f"   Tier: {model.tier.value}")
            click.echo(f"   Cost: ${model.cost_per_1k_input_tokens:.4f}/${model.cost_per_1k_output_tokens:.4f} per 1K tokens")
            click.echo(f"   Reasoning: {model.reasoning_score:.2f} | Speed: {model.speed_score:.2f}")
            click.echo()
    
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()


@llm_cli.command(name='cost-summary')
@click.option('--session-id', '-s', help='Filter by session ID')
@click.option('--profile-id', '-p', help='Filter by profile ID')
@click.option('--days', '-d', type=int, help='Number of days to look back')
def cost_summary(session_id: Optional[str], profile_id: Optional[str], days: Optional[int]):
    """Show cost summary and statistics."""
    try:
        registry = ModelRegistry()
        tracker = CostTracker(registry, storage_path="logs/llm_usage.json")
        
        if session_id:
            # Session-specific costs
            total_cost = tracker.get_session_cost(session_id)
            tokens = tracker.get_session_tokens(session_id)
            breakdown = tracker.get_cost_breakdown(session_id=session_id)
            
            click.echo(f"\nSession Cost Summary: {session_id}\n")
            click.echo(f"Total Cost: ${total_cost:.4f}")
            click.echo(f"Tokens: {tokens['input']:,} input, {tokens['output']:,} output")
            
            if breakdown:
                click.echo("\nBreakdown by Model:")
                for model, cost in sorted(breakdown.items(), key=lambda x: x[1], reverse=True):
                    click.echo(f"  {model}: ${cost:.4f}")
        
        elif profile_id:
            # Profile-specific costs
            from datetime import timedelta
            time_range = timedelta(days=days) if days else None
            total_cost = tracker.get_profile_cost(profile_id, time_range)
            breakdown = tracker.get_cost_breakdown(profile_id=profile_id, time_range=time_range)
            
            time_str = f"last {days} days" if days else "all time"
            click.echo(f"\nProfile Cost Summary: {profile_id} ({time_str})\n")
            click.echo(f"Total Cost: ${total_cost:.4f}")
            
            if breakdown:
                click.echo("\nBreakdown by Model:")
                for model, cost in sorted(breakdown.items(), key=lambda x: x[1], reverse=True):
                    click.echo(f"  {model}: ${cost:.4f}")
        
        else:
            # Overall statistics
            stats = tracker.get_statistics()
            
            click.echo("\nOverall Cost Statistics\n")
            click.echo(f"Total Requests: {stats['global_stats']['total_requests']:,}")
            click.echo(f"Successful: {stats['global_stats']['successful_requests']:,}")
            click.echo(f"Failed: {stats['global_stats']['failed_requests']:,}")
            click.echo(f"Success Rate: {stats['success_rate']*100:.1f}%")
            click.echo(f"\nTotal Cost: ${stats['global_stats']['total_cost']:.2f}")
            click.echo(f"Avg Cost/Request: ${stats['average_cost_per_request']:.4f}")
            click.echo(f"\nTotal Tokens: {stats['global_stats']['total_input_tokens']:,} input, "
                      f"{stats['global_stats']['total_output_tokens']:,} output")
            click.echo(f"\nActive Sessions: {stats['active_sessions']}")
            click.echo(f"Active Profiles: {stats['active_profiles']}")
            click.echo(f"Models Used: {stats['models_used']}")
        
        click.echo()
    
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()


@llm_cli.command(name='set-budget')
@click.argument('entity_type', type=click.Choice(['session', 'profile', 'global']))
@click.argument('entity_id', required=False)
@click.argument('budget', type=float)
def set_budget(entity_type: str, entity_id: Optional[str], budget: float):
    """Set budget limit for a session, profile, or globally."""
    try:
        if budget <= 0:
            click.echo("Budget must be positive", err=True)
            raise click.Abort()
        
        registry = ModelRegistry()
        tracker = CostTracker(registry, storage_path="logs/llm_usage.json")
        
        if entity_type == 'session':
            if not entity_id:
                click.echo("Session ID required for session budget", err=True)
                raise click.Abort()
            tracker.set_session_budget(entity_id, budget)
            click.echo(f"Set session budget for {entity_id}: ${budget:.2f}")
        
        elif entity_type == 'profile':
            if not entity_id:
                click.echo("Profile ID required for profile budget", err=True)
                raise click.Abort()
            tracker.set_profile_budget(entity_id, budget)
            click.echo(f"Set profile budget for {entity_id}: ${budget:.2f}")
        
        else:  # global
            tracker.set_global_budget(budget)
            click.echo(f"Set global budget: ${budget:.2f}")
    
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()


@llm_cli.command(name='model-stats')
@click.argument('provider')
@click.argument('model_name')
def model_statistics(provider: str, model_name: str):
    """Show usage statistics for a specific model."""
    try:
        registry = ModelRegistry()
        tracker = CostTracker(registry, storage_path="logs/llm_usage.json")
        
        full_name = f"{provider}/{model_name}"
        stats = tracker.get_model_statistics(full_name)
        
        if not stats:
            click.echo(f"No usage data found for model: {full_name}")
            return
        
        click.echo(f"\nUsage Statistics: {full_name}\n")
        click.echo(f"Total Requests: {stats['total_requests']:,}")
        click.echo(f"Successful: {stats['successful_requests']:,}")
        click.echo(f"Failed: {stats['failed_requests']:,}")
        click.echo(f"Success Rate: {stats['success_rate']*100:.1f}%")
        click.echo(f"\nTotal Cost: ${stats['total_cost']:.4f}")
        click.echo(f"Avg Cost/Request: ${stats['average_cost_per_request']:.4f}")
        click.echo(f"\nTotal Tokens: {stats['total_tokens']:,}")
        click.echo(f"Avg Latency: {stats['average_latency_ms']:.1f}ms")
        click.echo()
    
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()


@llm_cli.command(name='registry-stats')
def registry_statistics():
    """Show model registry statistics."""
    try:
        registry = ModelRegistry()
        stats = registry.get_statistics()
        
        click.echo("\nModel Registry Statistics\n")
        click.echo(f"Total Models: {stats['total_models']}")
        
        click.echo("\nModels by Provider:")
        for provider, count in sorted(stats['models_by_provider'].items()):
            click.echo(f"  {provider}: {count}")
        
        click.echo("\nModels by Tier:")
        for tier, count in sorted(stats['models_by_tier'].items()):
            click.echo(f"  {tier}: {count}")
        
        click.echo()
    
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()


@llm_cli.command(name='cheapest')
@click.option('--capability', help='Filter by required capability')
def find_cheapest(capability: Optional[str]):
    """Find the cheapest available model."""
    try:
        registry = ModelRegistry()
        
        cap_enum = ModelCapability(capability.upper()) if capability else None
        model = registry.get_cheapest_model(capability=cap_enum)
        
        if not model:
            click.echo("No model found matching criteria.")
            return
        
        click.echo(f"\nCheapest Model:")
        if capability:
            click.echo(f"(with capability: {capability})\n")
        else:
            click.echo()
        
        click.echo(f"Model: {model.display_name}")
        click.echo(f"Full Name: {model.get_full_name()}")
        click.echo(f"Tier: {model.tier.value}")
        click.echo(f"Cost: ${model.cost_per_1k_input_tokens:.4f}/${model.cost_per_1k_output_tokens:.4f} per 1K tokens")
        click.echo()
    
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()


@llm_cli.command(name='fastest')
@click.option('--tier', type=click.Choice(['ENTRY', 'STANDARD', 'ADVANCED', 'PREMIUM']), help='Filter by tier')
def find_fastest(tier: Optional[str]):
    """Find the fastest available model."""
    try:
        registry = ModelRegistry()
        
        tier_enum = ModelTier(tier.upper()) if tier else None
        model = registry.get_fastest_model(tier=tier_enum)
        
        if not model:
            click.echo("No model found matching criteria.")
            return
        
        click.echo(f"\nFastest Model:")
        if tier:
            click.echo(f"(in tier: {tier})\n")
        else:
            click.echo()
        
        click.echo(f"Model: {model.display_name}")
        click.echo(f"Full Name: {model.get_full_name()}")
        click.echo(f"Tier: {model.tier.value}")
        click.echo(f"Speed Score: {model.speed_score:.2f}/1.0")
        click.echo(f"Cost: ${model.cost_per_1k_input_tokens:.4f}/${model.cost_per_1k_output_tokens:.4f} per 1K tokens")
        click.echo()
    
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    llm_cli()