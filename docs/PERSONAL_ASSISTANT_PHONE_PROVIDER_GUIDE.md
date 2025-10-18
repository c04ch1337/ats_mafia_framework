# Personal Assistant Phone Provider Integration Guide

## 📞 Overview

This guide explains how to integrate real phone providers with the Personal Assistant feature, enabling Puppet Master to make actual phone calls on your behalf.

## 🔌 Supported Providers

### 1. Mock Provider (Default)
- **Use Case**: Testing and development
- **Cost**: Free
- **Limitations**: Simulated calls only, no real phone connectivity
- **Setup**: No configuration needed (default)

### 2. Twilio
- **Use Case**: Production use, reliable service
- **Cost**: Pay-as-you-go (~$0.01-0.02 per minute)
- **Pros**: Excellent documentation, reliable, feature-rich
- **Cons**: Requires account setup, costs money
- **Recommended**: ✅ Yes, for most users

### 3. Plivo
- **Use Case**: Alternative to Twilio
- **Cost**: Similar to Twilio
- **Pros**: Good alternative, competitive pricing
- **Cons**: Slightly less documentation than Twilio
- **Recommended**: ✅ Yes, as Twilio alternative

---

## 🚀 Twilio Setup (Recommended)

### Step 1: Create Twilio Account

1. Go to [https://www.twilio.com/try-twilio](https://www.twilio.com/try-twilio)
2. Sign up for a free trial account
3. Verify your phone number and email

### Step 2: Get Your Credentials

1. Log in to Twilio Console: [https://console.twilio.com](https://console.twilio.com)
2. Find your **Account SID** and **Auth Token** on the dashboard
3. Copy these values - you'll need them for configuration

### Step 3: Get a Phone Number

1. Go to Phone Numbers → Buy a Number
2. Search for a number in your area code
3. Purchase the number (free with trial credit)
4. Note the phone number (format: +1234567890)

### Step 4: Configure ATS MAFIA

#### Option A: Using YAML Configuration

Edit `ats_mafia_framework/config/default.yaml`:

```yaml
voice:
  personal_assistant:
    enabled: true
    phone_provider: twilio
    from_number: "+1234567890"  # Your Twilio number
    
    twilio:
      account_sid: "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      auth_token: "your_auth_token_here"
      phone_number: "+1234567890"
```

#### Option B: Using Environment Variables

Create or edit `.env` file:

```bash
PERSONAL_ASSISTANT_ENABLED=true
PERSONAL_ASSISTANT_PHONE_PROVIDER=twilio

TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
```

### Step 5: Install Twilio SDK

```bash
pip install twilio
```

### Step 6: Test Connection

```python
from ats_mafia_framework.voice.personal_assistant_config import (
    initialize_personal_assistant_feature,
    PersonalAssistantConfig
)
from ats_mafia_framework.config.settings import FrameworkConfig

# Load configuration
config = FrameworkConfig()

# Initialize Personal Assistant
initialized = initialize_personal_assistant_feature(config)

if initialized:
    print("✅ Twilio integration successful!")
else:
    print("❌ Twilio integration failed")
```

### Step 7: Make Your First Call

```python
from ats_mafia_framework.voice.personal_assistant import (
    get_personal_assistant_manager,
    PersonalTaskType,
    PersonalPersona
)

pa_manager = get_personal_assistant_manager()

task_id = await pa_manager.create_task(
    user_id="your_user_id",
    task_type=PersonalTaskType.INFORMATION_INQUIRY,
    phone_number="+1-555-TEST-NUM",
    intent_description="Test call to verify hours",
    context={"inquiry_topic": "store hours"},
    persona=PersonalPersona.PROFESSIONAL_ASSISTANT,
    requires_approval=False
)

await pa_manager.execute_task(task_id)
```

---

## 🔧 Plivo Setup (Alternative)

### Step 1: Create Plivo Account

1. Go to [https://www.plivo.com/](https://www.plivo.com/)
2. Sign up for free trial
3. Verify your account

### Step 2: Get Credentials

1. Log in to Plivo Console
2. Find your **Auth ID** and **Auth Token**
3. Copy these values

### Step 3: Get a Phone Number

1. Go to Phone Numbers → Buy Number
2. Search and purchase a number
3. Note the phone number

### Step 4: Configure ATS MAFIA

#### YAML Configuration:

```yaml
voice:
  personal_assistant:
    enabled: true
    phone_provider: plivo
    from_number: "+1234567890"
    
    plivo:
      auth_id: "MAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      auth_token: "your_auth_token_here"
      phone_number: "+1234567890"
```

#### Environment Variables:

```bash
PERSONAL_ASSISTANT_ENABLED=true
PERSONAL_ASSISTANT_PHONE_PROVIDER=plivo

PLIVO_AUTH_ID=MAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
PLIVO_AUTH_TOKEN=your_auth_token_here
PLIVO_PHONE_NUMBER=+1234567890
```

### Step 5: Install Plivo SDK

```bash
pip install plivo
```

---

## 🛠️ Implementation Guide

### Creating a Real Phone Provider (Twilio Example)

Create `ats_mafia_framework/voice/providers/twilio_provider.py`:

```python
"""Twilio phone provider implementation."""

import logging
from typing import Optional
from twilio.rest import Client
from ..phone import PhoneCall, CallState
from ..core import AudioSegment

class TwilioProvider:
    """Twilio VoIP provider implementation."""
    
    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        self.client = Client(account_sid, auth_token)
        self.from_number = from_number
        self.logger = logging.getLogger("twilio_provider")
    
    async def make_call(self, to_number: str, call_id: str) -> bool:
        """Initiate a call using Twilio."""
        try:
            call = self.client.calls.create(
                to=to_number,
                from_=self.from_number,
                url='http://your-server.com/voice/twiml',  # TwiML endpoint
                status_callback='http://your-server.com/voice/status',
                record=True
            )
            
            self.logger.info(f"Twilio call initiated: {call.sid}")
            return True
            
        except Exception as e:
            self.logger.error(f"Twilio call failed: {e}")
            return False
    
    async def end_call(self, call_id: str) -> bool:
        """End a Twilio call."""
        try:
            # Implement call termination
            return True
        except Exception as e:
            self.logger.error(f"Failed to end call: {e}")
            return False
    
    async def send_audio(self, call_id: str, audio: AudioSegment) -> bool:
        """Send audio to active call."""
        try:
            # Convert audio to format Twilio accepts
            # Send via TwiML or stream
            return True
        except Exception as e:
            self.logger.error(f"Failed to send audio: {e}")
            return False
```

### Integrating Provider into PhoneCallManager

Update `ats_mafia_framework/voice/phone.py` to support provider selection:

```python
from .providers.twilio_provider import TwilioProvider
from .providers.plivo_provider import PlivoProvider

class PhoneCallManager:
    def __init__(self, config, audit_logger=None):
        # ... existing code ...
        
        # Select provider based on configuration
        provider_type = config.get('voice.personal_assistant.phone_provider', 'mock')
        
        if provider_type == 'twilio':
            self.voip_provider = TwilioProvider(
                account_sid=config.get('voice.personal_assistant.twilio.account_sid'),
                auth_token=config.get('voice.personal_assistant.twilio.auth_token'),
                from_number=config.get('voice.personal_assistant.twilio.phone_number')
            )
        elif provider_type == 'plivo':
            self.voip_provider = PlivoProvider(
                auth_id=config.get('voice.personal_assistant.plivo.auth_id'),
                auth_token=config.get('voice.personal_assistant.plivo.auth_token'),
                from_number=config.get('voice.personal_assistant.plivo.phone_number')
            )
        else:
            self.voip_provider = MockVoIPProvider(config)
```

---

## 🎯 TwiML Integration (Twilio)

### What is TwiML?

TwiML (Twilio Markup Language) is XML used to tell Twilio what to do during calls.

### Basic TwiML Server Setup

Create a web server to handle Twilio webhooks:

```python
from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse

app = Flask(__name__)

@app.route('/voice/twiml', methods=['POST'])
def voice():
    """Handle incoming call or provide instructions."""
    response = VoiceResponse()
    
    # Play a message
    response.say(
        "Hello, I'm calling on behalf of John Doe.",
        voice='Polly.Joanna',
        language='en-US'
    )
    
    # Gather input
    gather = response.gather(
        input='speech',
        action='/voice/process',
        timeout=5
    )
    gather.say("How can I help you today?")
    
    return Response(str(response), mimetype='text/xml')

@app.route('/voice/process', methods=['POST'])
def process():
    """Process speech input."""
    speech_result = request.form.get('SpeechResult', '')
    
    response = VoiceResponse()
    response.say(f"You said: {speech_result}")
    
    return Response(str(response), mimetype='text/xml')

@app.route('/voice/status', methods=['POST'])
def status():
    """Handle call status updates."""
    call_sid = request.form.get('CallSid')
    call_status = request.form.get('CallStatus')
    
    print(f"Call {call_sid} status: {call_status}")
    
    return '', 200

if __name__ == '__main__':
    app.run(port=5000)
```

---

## 🔒 Security Best Practices

### 1. Credential Management
- **NEVER** commit credentials to version control
- Use environment variables or secure vaults
- Rotate credentials regularly
- Use separate credentials for dev/prod

### 2. Call Recording Compliance
- Inform participants calls are recorded
- Follow local laws (some states require two-party consent)
- Store recordings securely
- Implement retention policies

### 3. Rate Limiting
- Implement call volume limits
- Monitor for unusual patterns
- Set daily/weekly budgets
- Alert on threshold breaches

### 4. Data Privacy
- Encrypt recordings at rest
- Secure transcript storage
- Implement data retention policies
- GDPR/CCPA compliance

---

## 💰 Cost Estimation

### Twilio Pricing (as of 2025)
- **Outbound calls**: $0.013-0.022 per minute (US)
- **Phone number**: $1-2 per month
- **Recording storage**: $0.0025 per minute
- **Transcription**: $0.05 per minute (optional)

### Example Monthly Cost
```
Assumptions:
- 50 calls per month
- Average 3 minutes per call
- All calls recorded

Calculation:
- Calls: 50 × 3 min × $0.015/min = $2.25
- Number rental: $1.00
- Recording: 150 min × $0.0025/min = $0.38
───────────────────────────────────────────
Total: ~$3.63/month
```

### Cost Optimization Tips
- Use local numbers (cheaper rates)
- Limit call duration (set max_call_duration)
- Disable recording for simple tasks
- Batch similar calls
- Monitor usage dashboards

---

## 🧪 Testing

### Test with Twilio Test Credentials

Twilio provides test credentials for development:

```python
# Test credentials (won't make real calls)
TWILIO_ACCOUNT_SID = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # Real SID
TWILIO_AUTH_TOKEN = "test_token"  # Use "test" mode
```

### Validation Checklist

Before production use:

- [ ] Credentials configured correctly
- [ ] Phone number verified and active
- [ ] TwiML server accessible from internet
- [ ] Webhooks configured in Twilio console
- [ ] Call recording enabled (if desired)
- [ ] Rate limiting configured
- [ ] Error handling tested
- [ ] Compliance requirements met
- [ ] Backup/failover configured

---

## 🐛 Troubleshooting

### Common Issues

#### 1. "Authentication Error"
**Problem**: Invalid credentials
**Solution**: 
- Verify Account SID and Auth Token
- Check for typos or extra spaces
- Ensure credentials are for correct account

#### 2. "Phone Number Not Verified"
**Problem**: Twilio trial account restrictions
**Solution**:
- Verify the destination number in Twilio console
- Upgrade to paid account for unrestricted calling

#### 3. "TwiML Fetch Failed"
**Problem**: Twilio can't reach your TwiML server
**Solution**:
- Ensure server is publicly accessible
- Check firewall rules
- Verify URL is correct
- Use ngrok for local development

#### 4. "No Audio on Call"
**Problem**: Audio streaming not working
**Solution**:
- Check audio format compatibility
- Verify bidirectional audio is enabled
- Review Twilio debugger logs

### Debug Mode

Enable detailed logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('twilio')
logger.setLevel(logging.DEBUG)
```

### Twilio Debugger

Access detailed call logs:
1. Go to Twilio Console → Monitor → Logs → Calls
2. View individual call details
3. Check for errors and warnings
4. Review audio quality metrics

---

## 📱 Advanced Features

### 1. Call Recording with Transcription

```python
call = client.calls.create(
    to=to_number,
    from_=from_number,
    url=twiml_url,
    record=True,
    recording_status_callback='http://your-server.com/recording-complete',
    transcribe=True,  # Enable transcription
    transcribe_callback='http://your-server.com/transcription-complete'
)
```

### 2. Interactive Voice Response (IVR)

```python
@app.route('/voice/twiml', methods=['POST'])
def ivr():
    response = VoiceResponse()
    
    gather = response.gather(
        num_digits=1,
        action='/voice/handle-key',
        timeout=10
    )
    gather.say('Press 1 for sales, 2 for support')
    
    return Response(str(response), mimetype='text/xml')
```

### 3. Conference Calls

```python
response = VoiceResponse()
dial = response.dial()
dial.conference(
    'MyConference',
    start_conference_on_enter=True,
    end_conference_on_exit=True
)
```

### 4. Call Queuing

```python
response = VoiceResponse()
response.enqueue('support_queue', wait_url='/wait-music')
```

---

## 🌐 Webhook Server Setup

### Using Flask (Simple)

```python
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse

app = Flask(__name__)

@app.route('/voice/twiml', methods=['POST'])
def handle_call():
    # Get call information
    from_number = request.form.get('From')
    to_number = request.form.get('To')
    call_sid = request.form.get('CallSid')
    
    # Generate response
    response = VoiceResponse()
    response.say("Hello, this is Puppet Master calling.")
    
    return str(response), 200, {'Content-Type': 'text/xml'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### Using ngrok for Development

```bash
# Install ngrok
npm install -g ngrok

# Start your Flask server
python webhook_server.py

# In another terminal, expose it
ngrok http 5000

# Use the ngrok URL in Twilio configuration
# Example: https://abc123.ngrok.io/voice/twiml
```

---

## 📊 Monitoring & Analytics

### Twilio Console Monitoring

1. **Live Calls**: View active calls in real-time
2. **Call Logs**: Review completed call details
3. **Usage Report**: Track monthly usage and costs
4. **Error Logs**: Identify and fix issues

### Custom Analytics Integration

```python
from ats_mafia_framework.voice.personal_assistant import get_personal_assistant_manager

pa_manager = get_personal_assistant_manager()

# Get statistics
stats = pa_manager.get_statistics()

print(f"Total Tasks: {stats['total_tasks']}")
print(f"Success Rate: {stats['success_rate']:.1%}")
print(f"Average Duration: {stats['total_call_duration'] / stats['completed_tasks']:.2f}s")
```

---

## 🔐 Compliance & Legal

### Important Considerations

1. **Call Recording Consent**
   - Check local laws (one-party vs two-party consent)
   - Announce recording at call start
   - Provide opt-out option

2. **TCPA Compliance** (US)
   - Don't call cell phones without consent
   - Respect Do Not Call lists
   - Provide identification
   - Honor opt-out requests

3. **GDPR** (EU)
   - Get explicit consent
   - Provide data access
   - Allow data deletion
   - Document processing

4. **Data Retention**
   - Define retention periods
   - Implement auto-deletion
   - Secure storage
   - Audit access

### Compliance Checklist

- [ ] Recording disclosure implemented
- [ ] Consent mechanism in place
- [ ] Do Not Call list checking
- [ ] Caller ID properly configured
- [ ] Opt-out process documented
- [ ] Data retention policy defined
- [ ] Privacy policy updated
- [ ] Legal review completed

---

## 🚨 Emergency Procedures

### Call Failure Handling

```python
try:
    success = await pa_manager.execute_task(task_id)
except Exception as e:
    # Log error
    logger.error(f"Call failed: {e}")
    
    # Notify user
    send_notification(f"Call failed: {task.config.intent_description}")
    
    # Optionally retry
    if should_retry(task):
        await schedule_retry(task_id, delay_seconds=300)
```

### Human Takeover

```python
# If call goes poorly, allow human takeover
def enable_human_takeover(call_id: str) -> str:
    """
    Transfer call to human.
    
    Returns URL for human to join call.
    """
    # Generate conference room
    # Return join URL for human
    return "https://your-server.com/join-call/{call_id}"
```

---

## 📚 Additional Resources

### Official Documentation
- **Twilio**: [https://www.twilio.com/docs](https://www.twilio.com/docs)
- **Plivo**: [https://www.plivo.com/docs](https://www.plivo.com/docs)

### Helpful Tutorials
- Twilio Quickstart: Voice calls with Python
- Plivo Voice API Getting Started
- TwiML Best Practices

### Support
- Twilio Support: Available 24/7
- Plivo Support: Business hours
- Community Forums: Active communities for both

---

## ✅ Quick Reference

### Twilio Setup Summary
```bash
# 1. Install SDK
pip install twilio

# 2. Set environment variables
export TWILIO_ACCOUNT_SID="ACxxxx"
export TWILIO_AUTH_TOKEN="your_token"
export TWILIO_PHONE_NUMBER="+1234567890"

# 3. Enable in config
voice.personal_assistant.enabled: true
voice.personal_assistant.phone_provider: twilio

# 4. Initialize and use
python -m ats_mafia_framework.examples.personal_assistant_examples
```

### Plivo Setup Summary
```bash
# 1. Install SDK
pip install plivo

# 2. Set environment variables
export PLIVO_AUTH_ID="MAxxxx"
export PLIVO_AUTH_TOKEN="your_token"
export PLIVO_PHONE_NUMBER="+1234567890"

# 3. Enable in config
voice.personal_assistant.enabled: true
voice.personal_assistant.phone_provider: plivo

# 4. Initialize and use
python -m ats_mafia_framework.examples.personal_assistant_examples
```

---

**Last Updated**: October 2025  
**Maintained By**: ATS MAFIA Framework Team  
**Status**: Production Ready (with proper provider setup)