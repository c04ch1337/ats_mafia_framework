# ATS MAFIA UI - Advanced Training Simulation Interface

## Overview

The ATS MAFIA UI provides a comprehensive, immersive web-based interface for the Advanced Training Simulation Mafia framework. This interface delivers a professional, mafia-themed training environment with real-time monitoring, profile management, scenario control, and detailed reporting capabilities.

## Features

### 🎯 Core Functionality
- **Don's Office Dashboard**: Central command center with real-time metrics and system overview
- **Profile Management**: Create, edit, and manage specialized training profiles (Red Team, Blue Team, Social Engineer)
- **Scenario Management**: Design and deploy custom training scenarios
- **Situation Room**: Live training session monitoring and control
- **After-Action Reports**: Comprehensive performance analytics and reporting

### 🎨 Design System
- **Mafia Theme**: Immersive charcoal, red, and gold color scheme
- **Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **Modern UI Components**: Professional cards, modals, forms, and interactive elements
- **Accessibility**: WCAG compliant with semantic HTML and ARIA support

### 🚀 Technical Features
- **Real-time Updates**: WebSocket integration for live data streaming
- **API Integration**: RESTful API client with authentication and error handling
- **Component Architecture**: Modular, reusable JavaScript components
- **Performance Optimized**: Lazy loading, debouncing, and efficient rendering

## File Structure

```
ats_mafia_framework/ui/
├── index.html                 # Main dashboard ("Don's Office")
├── profiles.html              # Profile management interface
├── scenarios.html             # Scenario management interface
├── training.html              # Situation Room (live training)
├── reports.html               # After-Action Reports
├── css/
│   ├── ats-theme.css          # Core theme and design system
│   ├── components.css         # UI components styling
│   └── dashboard.css          # Dashboard-specific styles
├── js/
│   ├── api-client.js          # RESTful API integration
│   ├── websocket-client.js    # Real-time WebSocket client
│   ├── components.js          # Reusable UI components
│   ├── dashboard.js           # Dashboard functionality
│   ├── profiles.js            # Profile management
│   ├── scenarios.js           # Scenario management
│   ├── training.js            # Training session control
│   ├── reports.js             # Reporting and analytics
│   └── main.js                # Application initialization
├── assets/
│   ├── images/                # Static images and icons
│   └── fonts/                 # Custom fonts
└── README.md                  # This documentation
```

## Installation & Setup

### Prerequisites
- Modern web browser (Chrome, Firefox, Safari, Edge)
- ATS MAFIA backend server running
- Node.js (for development)

### Development Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ats_mafia_framework/ui
   ```

2. **Install dependencies** (if using Node.js for development):
   ```bash
   npm install
   ```

3. **Configure API endpoints**:
   Edit `js/main.js` to set the correct API base URL:
   ```javascript
   this.config = {
       apiBaseURL: 'http://localhost:8000/api/v1',
       websocketURL: 'ws://localhost:8000/ws',
       // ... other config
   };
   ```

4. **Start development server** (optional):
   ```bash
   npm run dev
   ```

5. **Open in browser**:
   Navigate to `http://localhost:3000` or open `index.html` directly

### Production Deployment

1. **Build for production**:
   ```bash
   npm run build
   ```

2. **Deploy to web server**:
   Copy the entire `ui/` directory to your web server's document root

3. **Configure server**:
   Ensure your server supports:
   - HTTPS (recommended for production)
   - WebSocket connections
   - Proper MIME types for static files

## Usage Guide

### Dashboard (Don's Office)

The main dashboard provides:
- **System Overview**: Real-time status and metrics
- **Active Sessions**: Monitor current training sessions
- **Performance Charts**: Visual analytics and trends
- **Quick Actions**: Launch profiles, create scenarios, view reports

### Profile Management

Create and manage training profiles:
1. **Create Profile**: Click "Create Profile" to add new profiles
2. **Profile Types**: Red Team, Blue Team, Social Engineer
3. **Configuration**: Set skill levels, specializations, and parameters
4. **Activation**: Start/stop profiles for training sessions

### Scenario Management

Design training scenarios:
1. **Create Scenario**: Define objectives, difficulty, and configuration
2. **Categories**: Penetration Testing, Social Engineering, Defense, Forensics
3. **Import/Export**: Share scenarios between instances

### Situation Room

Live training monitoring:
1. **Start Session**: Launch new training sessions
2. **Monitor**: Real-time session observation and control
3. **Logs**: Live activity feeds and event tracking
4. **Intervention**: Pause, resume, or modify active sessions

### After-Action Reports

Comprehensive reporting:
1. **Generate Reports**: Create performance, session, and trend reports
2. **Analytics**: Visual charts and statistical analysis
3. **Export**: Download reports in PDF, HTML, or JSON format

## API Integration

### Authentication
The UI automatically handles authentication tokens:
```javascript
// Login
await window.atsAPI.login({
    username: 'admin',
    password: 'password'
});

// Token is automatically stored and refreshed
```

### WebSocket Events
Real-time updates via WebSocket:
```javascript
// Listen for training updates
window.atsWebSocket.subscribe('training_update', (data) => {
    console.log('Training update:', data);
});

// Send commands
window.atsWebSocket.sendTrainingCommand(sessionId, 'pause');
```

### Custom API Calls
Direct API integration:
```javascript
// Get profiles
const profiles = await window.atsAPI.getProfiles();

// Create new scenario
const scenario = await window.atsAPI.createScenario({
    name: 'Advanced Penetration Test',
    difficulty: 'expert',
    // ... other fields
});
```

## Customization

### Theme Customization
Modify `css/ats-theme.css` to customize colors and styling:
```css
:root {
    --color-primary-dark: #1a1a1a;        /* Charcoal black */
    --color-accent-red: #b71c1c;          /* Deep red */
    --color-accent-gold: #ffd700;         /* Gold */
    /* ... other variables */
}
```

### Component Development
Create new components in `js/components.js`:
```javascript
class CustomComponent {
    constructor(element, options) {
        this.element = element;
        this.options = options;
        this.init();
    }
    
    init() {
        // Component initialization
    }
}
```

### Adding New Pages
1. Create HTML file in root directory
2. Add corresponding JavaScript file in `js/`
3. Update navigation in all HTML files
4. Add page-specific CSS if needed

## Browser Support

- **Chrome**: 90+
- **Firefox**: 88+
- **Safari**: 14+
- **Edge**: 90+

### Required Features
- ES6+ JavaScript support
- CSS Grid and Flexbox
- WebSocket API
- Local Storage
- Fetch API

## Security Considerations

- **HTTPS**: Required for production deployments
- **CORS**: Configure backend to allow UI domain
- **Authentication**: Tokens stored securely in localStorage
- **XSS Protection**: Input sanitization and content security policy
- **CSRF Protection**: Include anti-CSRF tokens in API calls

## Performance Optimization

- **Lazy Loading**: Components and data loaded on demand
- **Debouncing**: Search and filter inputs debounced
- **Caching**: API responses cached where appropriate
- **Minification**: CSS and JavaScript minified in production
- **Compression**: Gzip compression enabled on server

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Check backend server is running
   - Verify WebSocket URL configuration
   - Check firewall/proxy settings

2. **API Authentication Errors**
   - Verify backend authentication endpoints
   - Check token storage and refresh logic
   - Ensure CORS headers are properly configured

3. **Performance Issues**
   - Check browser console for JavaScript errors
   - Monitor network requests in developer tools
   - Verify server response times

4. **Styling Issues**
   - Clear browser cache
   - Check CSS file loading in network tab
   - Verify font loading and CORS policies

### Debug Mode
Enable debug logging:
```javascript
// In browser console
localStorage.setItem('ats_debug', 'true');
location.reload();
```

## Contributing

1. **Fork** the repository
2. **Create** feature branch
3. **Make** changes following coding standards
4. **Test** thoroughly across browsers
5. **Submit** pull request with description

### Coding Standards
- Use ES6+ JavaScript features
- Follow BEM CSS naming convention
- Include JSDoc comments for functions
- Maintain responsive design principles
- Test accessibility with screen readers

## License

This project is part of the ATS MAFIA framework and is subject to the same license terms.

## Support

For technical support and questions:
- Create issues in the project repository
- Consult the main ATS MAFIA documentation
- Contact the development team

---

**ATS MAFIA UI** - Professional Training Simulation Interface
© 2024 Advanced Training Simulation Mafia Framework