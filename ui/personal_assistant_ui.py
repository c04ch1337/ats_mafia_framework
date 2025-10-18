"""
ATS MAFIA Framework Personal Assistant UI Component

This module provides UI components for the Personal Assistant feature.
"""

from typing import Dict, Any, List, Optional
import json


class PersonalAssistantUI:
    """UI handler for Personal Assistant features."""
    
    def __init__(self):
        """Initialize Personal Assistant UI."""
        self.component_id = "personal_assistant"
        self.enabled = True
    
    def get_ui_config(self) -> Dict[str, Any]:
        """
        Get UI configuration for Personal Assistant.
        
        Returns:
            UI configuration dictionary
        """
        return {
            'component_id': self.component_id,
            'title': 'Puppet Master - Personal Assistant',
            'description': 'Make calls and handle tasks on your behalf',
            'icon': 'phone_assistant',
            'enabled': self.enabled,
            'sections': [
                self._get_task_creation_section(),
                self._get_task_history_section(),
                self._get_preferences_section()
            ],
            'quick_actions': self._get_quick_actions(),
            'task_types': self._get_task_type_options(),
            'personas': self._get_persona_options()
        }
    
    def _get_task_creation_section(self) -> Dict[str, Any]:
        """Get task creation section configuration."""
        return {
            'section_id': 'task_creation',
            'title': 'New Personal Task',
            'type': 'form',
            'fields': [
                {
                    'id': 'intent_description',
                    'type': 'textarea',
                    'label': 'What would you like me to do?',
                    'placeholder': 'Example: Book a dentist appointment for next week, morning preferred',
                    'required': True,
                    'rows': 3,
                    'examples': [
                        'Book dentist appointment for next Tuesday morning',
                        'Call auto shop and ask about oil change pricing',
                        'Check restaurant hours for tonight',
                        'Call Mom and let her know I\'ll visit Sunday at 2 PM'
                    ]
                },
                {
                    'id': 'task_type',
                    'type': 'select',
                    'label': 'Task Type',
                    'required': True,
                    'options': [
                        {'value': 'appointment_booking', 'label': '📅 Appointment Booking'},
                        {'value': 'information_inquiry', 'label': '❓ Information Inquiry'},
                        {'value': 'service_issue', 'label': '🔧 Service Issue'},
                        {'value': 'social_call', 'label': '👥 Social Call'},
                        {'value': 'custom', 'label': '✏️ Custom Task'}
                    ],
                    'default': 'appointment_booking'
                },
                {
                    'id': 'phone_number',
                    'type': 'tel',
                    'label': 'Phone Number',
                    'placeholder': '+1-555-123-4567',
                    'required': True,
                    'pattern': '^[+]?[0-9\\-\\s()]+$',
                    'help_text': 'Number to call (include country code for international)'
                },
                {
                    'id': 'context',
                    'type': 'key_value',
                    'label': 'Additional Context (Optional)',
                    'help_text': 'Provide extra details like account numbers, preferred times, etc.',
                    'fields': [
                        {'key': 'user_name', 'label': 'Your Name', 'type': 'text'},
                        {'key': 'preferred_time', 'label': 'Preferred Time', 'type': 'text'},
                        {'key': 'account_number', 'label': 'Account Number', 'type': 'text'},
                        {'key': 'reference_number', 'label': 'Reference Number', 'type': 'text'}
                    ]
                },
                {
                    'id': 'persona',
                    'type': 'select',
                    'label': 'Voice Persona',
                    'required': True,
                    'options': [
                        {'value': 'professional_assistant', 'label': '💼 Professional Assistant'},
                        {'value': 'friendly_representative', 'label': '😊 Friendly Representative'},
                        {'value': 'formal_business', 'label': '🎩 Formal Business'},
                        {'value': 'casual_helper', 'label': '👋 Casual Helper'}
                    ],
                    'default': 'professional_assistant',
                    'help_text': 'Choose the voice style for this call'
                },
                {
                    'id': 'requires_approval',
                    'type': 'checkbox',
                    'label': 'Require my approval before calling',
                    'default': True,
                    'help_text': 'Review the script before the call is made'
                }
            ],
            'actions': [
                {
                    'id': 'create_task',
                    'label': '📝 Generate Script',
                    'type': 'primary',
                    'action': 'create_task',
                    'tooltip': 'Create task and generate call script for review'
                }
            ]
        }
    
    def _get_task_history_section(self) -> Dict[str, Any]:
        """Get task history section configuration."""
        return {
            'section_id': 'task_history',
            'title': 'Task History',
            'type': 'table',
            'columns': [
                {'id': 'created_at', 'label': 'Created', 'type': 'datetime', 'sortable': True},
                {'id': 'task_type', 'label': 'Type', 'type': 'badge', 'width': '120px'},
                {'id': 'intent_description', 'label': 'Description', 'type': 'text'},
                {'id': 'phone_number', 'label': 'Number', 'type': 'text', 'width': '140px'},
                {'id': 'status', 'label': 'Status', 'type': 'status', 'width': '100px'},
                {'id': 'duration', 'label': 'Duration', 'type': 'duration', 'width': '80px'},
                {'id': 'actions', 'label': 'Actions', 'type': 'actions', 'width': '120px'}
            ],
            'row_actions': [
                {'id': 'view_details', 'label': 'View', 'icon': 'eye'},
                {'id': 'view_transcript', 'label': 'Transcript', 'icon': 'file-text'},
                {'id': 'play_recording', 'label': 'Play', 'icon': 'play'},
                {'id': 'retry', 'label': 'Retry', 'icon': 'refresh'}
            ],
            'filters': [
                {
                    'id': 'status_filter',
                    'type': 'multi_select',
                    'label': 'Status',
                    'options': [
                        {'value': 'pending', 'label': 'Pending'},
                        {'value': 'awaiting_approval', 'label': 'Awaiting Approval'},
                        {'value': 'approved', 'label': 'Approved'},
                        {'value': 'calling', 'label': 'Calling'},
                        {'value': 'completed', 'label': 'Completed'},
                        {'value': 'failed', 'label': 'Failed'},
                        {'value': 'cancelled', 'label': 'Cancelled'}
                    ]
                },
                {
                    'id': 'date_filter',
                    'type': 'date_range',
                    'label': 'Date Range'
                }
            ],
            'pagination': {
                'page_size': 25,
                'show_page_size_selector': True,
                'page_size_options': [10, 25, 50, 100]
            }
        }
    
    def _get_preferences_section(self) -> Dict[str, Any]:
        """Get preferences section configuration."""
        return {
            'section_id': 'preferences',
            'title': 'Personal Assistant Preferences',
            'type': 'form',
            'fields': [
                {
                    'id': 'default_persona',
                    'type': 'select',
                    'label': 'Default Voice Persona',
                    'options': [
                        {'value': 'professional_assistant', 'label': '💼 Professional Assistant'},
                        {'value': 'friendly_representative', 'label': '😊 Friendly Representative'},
                        {'value': 'formal_business', 'label': '🎩 Formal Business'},
                        {'value': 'casual_helper', 'label': '👋 Casual Helper'}
                    ],
                    'default': 'professional_assistant'
                },
                {
                    'id': 'auto_record',
                    'type': 'checkbox',
                    'label': 'Automatically record all calls',
                    'default': True,
                    'help_text': 'Recommended for review and compliance'
                },
                {
                    'id': 'require_approval_default',
                    'type': 'checkbox',
                    'label': 'Require approval for all tasks by default',
                    'default': True,
                    'help_text': 'You can override this for individual tasks'
                },
                {
                    'id': 'max_call_duration',
                    'type': 'number',
                    'label': 'Maximum Call Duration (minutes)',
                    'min': 1,
                    'max': 30,
                    'default': 10,
                    'help_text': 'Calls will be automatically ended after this time'
                },
                {
                    'id': 'notification_preferences',
                    'type': 'multi_select',
                    'label': 'Notify me when:',
                    'options': [
                        {'value': 'task_created', 'label': 'Task is created'},
                        {'value': 'task_awaiting_approval', 'label': 'Task needs approval'},
                        {'value': 'call_started', 'label': 'Call starts'},
                        {'value': 'call_completed', 'label': 'Call completes'},
                        {'value': 'task_failed', 'label': 'Task fails'}
                    ],
                    'default': ['task_awaiting_approval', 'call_completed', 'task_failed']
                }
            ],
            'actions': [
                {
                    'id': 'save_preferences',
                    'label': '💾 Save Preferences',
                    'type': 'primary',
                    'action': 'save_preferences'
                }
            ]
        }
    
    def _get_quick_actions(self) -> List[Dict[str, Any]]:
        """Get quick action configurations."""
        return [
            {
                'id': 'quick_appointment',
                'label': 'Quick Appointment',
                'icon': 'calendar',
                'description': 'Book an appointment quickly',
                'task_type': 'appointment_booking',
                'persona': 'professional_assistant'
            },
            {
                'id': 'quick_info',
                'label': 'Get Info',
                'icon': 'info',
                'description': 'Make a quick information inquiry',
                'task_type': 'information_inquiry',
                'persona': 'friendly_representative'
            },
            {
                'id': 'service_issue',
                'label': 'Report Issue',
                'icon': 'alert-circle',
                'description': 'Report a service problem',
                'task_type': 'service_issue',
                'persona': 'professional_assistant'
            }
        ]
    
    def _get_task_type_options(self) -> List[Dict[str, Any]]:
        """Get task type options with descriptions."""
        return [
            {
                'value': 'appointment_booking',
                'label': 'Appointment Booking',
                'icon': '📅',
                'description': 'Schedule, cancel, or reschedule appointments',
                'examples': [
                    'Book a dental cleaning for next week',
                    'Cancel my haircut appointment on Friday',
                    'Reschedule doctor appointment to next month'
                ]
            },
            {
                'value': 'information_inquiry',
                'label': 'Information Inquiry',
                'icon': '❓',
                'description': 'Get information about hours, pricing, availability',
                'examples': [
                    'What are the store hours today?',
                    'How much do they charge for an oil change?',
                    'Do they have this product in stock?'
                ]
            },
            {
                'value': 'service_issue',
                'label': 'Service Issue',
                'icon': '🔧',
                'description': 'Report problems and request resolution',
                'examples': [
                    'My internet has been down for 2 days',
                    'I was charged incorrectly on my bill',
                    'My delivery is late, need tracking update'
                ]
            },
            {
                'value': 'social_call',
                'label': 'Social Call',
                'icon': '👥',
                'description': 'RSVP, relay messages, coordinate',
                'examples': [
                    'RSVP yes to the party on Saturday',
                    'Tell Mom I\'ll visit on Sunday at 2 PM',
                    'Ask if they\'re available for lunch next week'
                ]
            },
            {
                'value': 'custom',
                'label': 'Custom Task',
                'icon': '✏️',
                'description': 'Any other phone task you need handled',
                'examples': [
                    'Custom task based on your specific needs'
                ]
            }
        ]
    
    def _get_persona_options(self) -> List[Dict[str, Any]]:
        """Get persona options with descriptions."""
        return [
            {
                'value': 'professional_assistant',
                'label': 'Professional Assistant',
                'icon': '💼',
                'description': 'Formal, business-like tone. Best for appointments and professional matters.',
                'voice_characteristics': 'Clear, confident, respectful'
            },
            {
                'value': 'friendly_representative',
                'label': 'Friendly Representative',
                'icon': '😊',
                'description': 'Warm, approachable tone. Good for social calls and casual inquiries.',
                'voice_characteristics': 'Warm, personable, helpful'
            },
            {
                'value': 'formal_business',
                'label': 'Formal Business',
                'icon': '🎩',
                'description': 'Very formal, corporate tone. For serious business matters.',
                'voice_characteristics': 'Formal, authoritative, precise'
            },
            {
                'value': 'casual_helper',
                'label': 'Casual Helper',
                'icon': '👋',
                'description': 'Relaxed, friendly tone. For informal situations.',
                'voice_characteristics': 'Relaxed, conversational, easygoing'
            }
        ]
    
    def get_task_detail_modal(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get task detail modal configuration.
        
        Args:
            task_data: Task data to display
            
        Returns:
            Modal configuration
        """
        return {
            'modal_id': 'task_detail',
            'title': f"Task Details - {task_data.get('task_id', 'Unknown')}",
            'size': 'large',
            'sections': [
                {
                    'title': 'Task Information',
                    'type': 'info',
                    'fields': [
                        {'label': 'Task ID', 'value': task_data.get('task_id')},
                        {'label': 'Type', 'value': task_data.get('task_type')},
                        {'label': 'Status', 'value': task_data.get('status'), 'type': 'badge'},
                        {'label': 'Phone Number', 'value': task_data.get('phone_number')},
                        {'label': 'Created', 'value': task_data.get('created_at'), 'type': 'datetime'},
                        {'label': 'Duration', 'value': task_data.get('duration'), 'type': 'duration'}
                    ]
                },
                {
                    'title': 'Call Script',
                    'type': 'code',
                    'content': task_data.get('script', 'No script generated'),
                    'language': 'text',
                    'editable': task_data.get('status') == 'awaiting_approval'
                },
                {
                    'title': 'Transcript',
                    'type': 'transcript',
                    'content': task_data.get('transcript', 'No transcript available'),
                    'show_if': task_data.get('transcript') is not None
                },
                {
                    'title': 'Call Recording',
                    'type': 'audio_player',
                    'audio_url': task_data.get('recording_file'),
                    'show_if': task_data.get('recording_file') is not None
                },
                {
                    'title': 'Results',
                    'type': 'json',
                    'content': task_data.get('result', {}),
                    'show_if': task_data.get('result') is not None
                }
            ],
            'actions': self._get_task_detail_actions(task_data)
        }
    
    def _get_task_detail_actions(self, task_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get actions available for task detail modal."""
        status = task_data.get('status')
        actions = []
        
        if status == 'awaiting_approval':
            actions.extend([
                {'id': 'approve', 'label': '✅ Approve & Execute', 'type': 'success'},
                {'id': 'edit_script', 'label': '✏️ Edit Script', 'type': 'secondary'},
                {'id': 'reject', 'label': '❌ Cancel', 'type': 'danger'}
            ])
        elif status == 'approved':
            actions.extend([
                {'id': 'execute', 'label': '📞 Make Call Now', 'type': 'primary'},
                {'id': 'cancel', 'label': '❌ Cancel', 'type': 'danger'}
            ])
        elif status == 'failed':
            actions.extend([
                {'id': 'retry', 'label': '🔄 Retry', 'type': 'primary'},
                {'id': 'view_error', 'label': '⚠️ View Error', 'type': 'secondary'}
            ])
        elif status == 'completed':
            actions.extend([
                {'id': 'view_transcript', 'label': '📄 View Transcript', 'type': 'secondary'},
                {'id': 'download_recording', 'label': '⬇️ Download Recording', 'type': 'secondary'},
                {'id': 'retry', 'label': '🔄 Call Again', 'type': 'tertiary'}
            ])
        
        actions.append({'id': 'close', 'label': 'Close', 'type': 'tertiary'})
        return actions
    
    def get_approval_modal(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get task approval modal configuration.
        
        Args:
            task_data: Task data for approval
            
        Returns:
            Modal configuration
        """
        return {
            'modal_id': 'task_approval',
            'title': 'Review & Approve Call',
            'size': 'large',
            'sections': [
                {
                    'type': 'alert',
                    'style': 'info',
                    'content': 'Review the generated script below. Puppet Master will use this script when making the call on your behalf.'
                },
                {
                    'title': 'Task Details',
                    'type': 'info_grid',
                    'fields': [
                        {'label': 'Calling', 'value': task_data.get('phone_number'), 'icon': 'phone'},
                        {'label': 'Purpose', 'value': task_data.get('intent_description'), 'icon': 'target'},
                        {'label': 'Persona', 'value': task_data.get('persona'), 'icon': 'user'}
                    ]
                },
                {
                    'title': 'Call Script',
                    'type': 'code_editor',
                    'content': task_data.get('script', ''),
                    'language': 'text',
                    'height': '300px',
                    'editable': True,
                    'help_text': 'You can edit this script if needed'
                },
                {
                    'type': 'alert',
                    'style': 'warning',
                    'content': '⚠️ This call will be recorded. Puppet Master will identify itself as calling on your behalf and will disclose its AI nature if asked.'
                }
            ],
            'actions': [
                {'id': 'approve', 'label': '✅ Approve & Make Call', 'type': 'success'},
                {'id': 'save_script', 'label': '💾 Save Changes', 'type': 'secondary'},
                {'id': 'cancel', 'label': '❌ Cancel Task', 'type': 'danger'},
                {'id': 'close', 'label': 'Close', 'type': 'tertiary'}
            ]
        }
    
    def get_agent_selection_integration(self) -> Dict[str, Any]:
        """
        Get configuration for integrating into agent selection dropdown.
        
        Returns:
            Agent selection integration config
        """
        return {
            'category': 'Personal Assistant',
            'agent': {
                'id': 'puppet_master_personal',
                'name': '🎭 Puppet Master - Personal',
                'icon': 'phone',
                'description': 'Make calls and appointments on my behalf',
                'type': 'personal_assistant'
            },
            'show_intent_box': True,
            'intent_box': {
                'label': 'What do you need me to do?',
                'placeholder': 'Example: Book dentist appointment for next week',
                'examples': [
                    'Book dentist appointment',
                    'Ask about store hours',
                    'Cancel my reservation',
                    'Check on my package delivery'
                ],
                'show_quick_actions': True,
                'quick_actions': self._get_quick_actions()
            },
            'configuration_button': {
                'label': '⚙️ Configure Personal Task',
                'action': 'open_personal_assistant_modal'
            }
        }
    
    def get_call_monitor_widget(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get real-time call monitoring widget configuration.
        
        Args:
            task_data: Active task data
            
        Returns:
            Widget configuration
        """
        return {
            'widget_id': 'call_monitor',
            'title': '📞 Call in Progress',
            'type': 'live_monitor',
            'status': 'active',
            'sections': [
                {
                    'type': 'status_bar',
                    'fields': [
                        {'label': 'Calling', 'value': task_data.get('phone_number'), 'icon': 'phone'},
                        {'label': 'Duration', 'value': '0:00', 'type': 'live_timer'},
                        {'label': 'Status', 'value': 'Connected', 'type': 'live_status'}
                    ]
                },
                {
                    'type': 'live_transcript',
                    'title': 'Live Conversation',
                    'height': '400px',
                    'auto_scroll': True
                },
                {
                    'type': 'audio_visualizer',
                    'show_waveform': True,
                    'show_volume_meter': True
                }
            ],
            'actions': [
                {'id': 'human_takeover', 'label': '🎤 Take Over Call', 'type': 'warning'},
                {'id': 'end_call', 'label': '📵 End Call', 'type': 'danger'},
                {'id': 'minimize', 'label': 'Minimize', 'type': 'tertiary'}
            ]
        }
    
    def to_json(self) -> str:
        """
        Convert UI configuration to JSON.
        
        Returns:
            JSON string of UI configuration
        """
        return json.dumps(self.get_ui_config(), indent=2)


# Create global instance
personal_assistant_ui = PersonalAssistantUI()


def get_personal_assistant_ui() -> PersonalAssistantUI:
    """
    Get the global Personal Assistant UI instance.
    
    Returns:
        PersonalAssistantUI instance
    """
    return personal_assistant_ui