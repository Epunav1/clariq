# Feedback & Support System Setup Guide

Users can submit feedback, bugs, complaints, and feature requests. You receive email notifications and can track all submissions.

---

## ✅ What's Included

- **Feedback Database**: SQLite storage for all submissions
- **Email Notifications**: Automatic emails to owner when feedback received
- **Ticket Tracking**: Track status of each feedback item (open → responded → closed)
- **User Confirmation**: Users get confirmation emails with ticket numbers
- **REST API**: Full API to submit, list, and manage feedback
- **Statistics**: Dashboard view of feedback by type, priority, status

---

## 🔧 Configuration

### Set These Environment Variables

```bash
# Required for email notifications
SMTP_HOST=smtp.gmail.com                    # Your SMTP server
SMTP_PORT=587                               # Usually 587 for Gmail
SMTP_USER=your-email@gmail.com              # Your email
SMTP_PASSWORD=your-app-password             # Gmail app password (not your regular password!)
SMTP_FROM=noreply@tryclariq.com            # From address (can be same as SMTP_USER)

# Optional but recommended
OWNER_EMAIL=you@example.com                 # Where you receive notifications
```

### Example: Gmail Setup

```bash
# 1. Enable 2FA on Gmail
# 2. Create App Password: 
#    https://myaccount.google.com/apppasswords
# 3. Add to Railway variables:
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=<16-character-app-password>
OWNER_EMAIL=your-email@gmail.com
```

### Example: SendGrid Setup

```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SG.xxxxxxxxxxxxxxxxxxxxx
SMTP_FROM=noreply@tryclariq.com
OWNER_EMAIL=you@example.com
```

---

## 🎯 How It Works

### User Submits Feedback

1. User fills feedback form (or calls API)
2. Feedback stored in database
3. **User receives confirmation email** with ticket number
4. **Owner receives notification email**

### Owner Reviews Feedback

1. Check /api/feedback to list all submissions
2. Review by type: `bug`, `feature`, `complaint`, `general`
3. Update status: `open` → `responded` → `closed`

### User Gets Response

1. Owner responds via API
2. **User automatically receives response email**

---

## 📡 API Endpoints

### Submit Feedback
```bash
POST /api/feedback/submit
Content-Type: application/json

{
  "user_email": "user@example.com",
  "user_name": "John Doe",
  "subject": "Bug in export feature",
  "message": "When I try to export more than 100 pilots, the file downloads incomplete. This happens consistently.",
  "feedback_type": "bug",
  "priority": "high"
}

Response:
{
  "feedback_id": 1,
  "status": "received",
  "message": "Thank you! We've received your feedback..."
}
```

### Get Feedback Status
```bash
GET /api/feedback/{feedback_id}

Response:
{
  "id": 1,
  "user_email": "user@example.com",
  "subject": "Bug in export feature",
  "status": "open",
  "priority": "high",
  "created_at": "2024-07-09T12:30:00",
  "response": null
}
```

### List All Feedback (Admin)
```bash
GET /api/feedback
GET /api/feedback?status=open

Response:
{
  "count": 3,
  "feedbacks": [
    {
      "id": 1,
      "user_email": "user@example.com",
      "subject": "Bug in export",
      "type": "bug",
      "status": "open",
      "priority": "high",
      "created_at": "2024-07-09T12:30:00"
    }
  ]
}
```

### Respond to Feedback (Admin)
```bash
POST /api/feedback/{feedback_id}/respond
Content-Type: application/json

{
  "response": "Thanks for reporting! We found the issue and fixed it in v2.1. Please update to get the fix."
}

Response:
{
  "status": "responded",
  "message": "Response sent to user"
}
```

### Close Feedback Ticket (Admin)
```bash
POST /api/feedback/{feedback_id}/close

Response:
{
  "status": "closed",
  "message": "Feedback ticket closed"
}
```

### Get Feedback Statistics (Admin)
```bash
GET /api/feedback/stats/summary

Response:
{
  "total": 12,
  "by_status": {
    "open": 5,
    "responded": 4,
    "closed": 3
  },
  "by_type": {
    "bug": 7,
    "feature": 3,
    "general": 2
  },
  "by_priority": {
    "normal": 9,
    "high": 2,
    "urgent": 1
  }
}
```

### Check Support System Status
```bash
GET /api/support/status

Response:
{
  "status": "operational",
  "feedback_system": "active",
  "email_notifications": "configured",
  "support_email": "you@example.com",
  "response_time": "24 hours"
}
```

---

## 🎨 Frontend Implementation

### Simple Feedback Form (HTML/JS)

```html
<!-- Feedback Button in Dashboard -->
<button onclick="openFeedbackForm()">📬 Send Feedback</button>

<div id="feedbackModal" style="display:none;">
  <h2>Send Us Your Feedback</h2>
  
  <form onsubmit="submitFeedback(event)">
    <div>
      <label>Your Email *</label>
      <input type="email" id="userEmail" required>
    </div>
    
    <div>
      <label>Your Name</label>
      <input type="text" id="userName">
    </div>
    
    <div>
      <label>Type *</label>
      <select id="feedbackType" required>
        <option value="general">General Feedback</option>
        <option value="bug">Report a Bug</option>
        <option value="feature">Feature Request</option>
        <option value="complaint">Submit a Complaint</option>
      </select>
    </div>
    
    <div>
      <label>Priority</label>
      <select id="priority">
        <option value="normal">Normal</option>
        <option value="high">High</option>
        <option value="urgent">Urgent</option>
      </select>
    </div>
    
    <div>
      <label>Subject *</label>
      <input type="text" id="subject" required placeholder="Brief summary">
    </div>
    
    <div>
      <label>Message *</label>
      <textarea id="message" required placeholder="Detailed description" rows="5"></textarea>
    </div>
    
    <button type="submit">Send Feedback</button>
  </form>
  
  <div id="feedbackResult" style="display:none; margin-top:20px; padding:10px; background:#e8f5e9; border-radius:5px;">
    <p id="resultText"></p>
  </div>
</div>

<script>
function openFeedbackForm() {
  document.getElementById('feedbackModal').style.display = 'block';
}

async function submitFeedback(e) {
  e.preventDefault();
  
  const feedbackData = {
    user_email: document.getElementById('userEmail').value,
    user_name: document.getElementById('userName').value,
    feedback_type: document.getElementById('feedbackType').value,
    subject: document.getElementById('subject').value,
    message: document.getElementById('message').value,
    priority: document.getElementById('priority').value
  };
  
  try {
    const response = await fetch('/api/feedback/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(feedbackData)
    });
    
    const result = await response.json();
    
    if (response.ok) {
      document.getElementById('resultText').textContent = 
        `✅ Feedback sent! Ticket #${result.feedback_id}. Check your email for confirmation.`;
      document.getElementById('feedbackResult').style.display = 'block';
      
      // Reset form
      setTimeout(() => {
        document.getElementById('feedbackModal').style.display = 'none';
        document.querySelector('form').reset();
      }, 2000);
    } else {
      throw new Error(result.detail);
    }
  } catch (error) {
    document.getElementById('resultText').textContent = 
      `❌ Error: ${error.message}`;
    document.getElementById('feedbackResult').style.display = 'block';
  }
}
</script>

<style>
#feedbackModal {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: white;
  padding: 30px;
  border-radius: 10px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  max-width: 500px;
  width: 90%;
  z-index: 1000;
}

#feedbackModal input,
#feedbackModal select,
#feedbackModal textarea {
  width: 100%;
  padding: 8px;
  margin: 5px 0 15px 0;
  border: 1px solid #ddd;
  border-radius: 5px;
  font-family: inherit;
}

#feedbackModal button {
  background: #007bff;
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

#feedbackModal button:hover {
  background: #0056b3;
}
</style>
```

---

## 📊 Best Practices

### For Users Submitting Feedback

1. **Be Specific**: Describe exactly what you experienced
2. **Include Steps**: "I clicked X, then Y happened"
3. **Set Priority**: Mark urgent issues as "high" or "urgent"
4. **Check Email**: You'll get confirmation with ticket number

### For You (Owner)

1. **Respond Quickly**: Aim for <24 hour response time
2. **Thank Them**: Acknowledge the feedback
3. **Set Expectations**: "We'll investigate and get back to you in 3 days"
4. **Close When Done**: Mark as closed after resolving
5. **Use Stats**: Check /api/feedback/stats/summary to identify patterns

### Common Issues

```
User reports: "Export is broken"
❌ Don't ignore
✅ Do: Reply within 24 hours, ask for specifics

User reports: "Slow API"
❌ Don't say "Works fine for me"
✅ Do: Check logs, ask for affected endpoint, offer help

Feedback marked "urgent"
❌ Don't deprioritize
✅ Do: Review within 4 hours, respond same day
```

---

## 🔐 Security Notes

- **Never** expose sensitive data in feedback
- **Validate** all inputs (email format, length, etc)
- **Rate limit** feedback submission (optional: 1 per user per hour)
- **Store securely** in encrypted database
- **Don't share** user feedback publicly without permission

---

## 📞 Support Email Setup

Add a support page to your dashboard:

```html
<div class="support-section">
  <h2>Need Help?</h2>
  <p><strong>Quick Help:</strong> Use the feedback form above</p>
  <p><strong>Email Support:</strong> support@tryclariq.com</p>
  <p><strong>Response Time:</strong> Within 24 hours</p>
  <p><strong>Urgent Issues:</strong> Mark as "Urgent" in feedback form</p>
</div>
```

---

## ✅ Setup Checklist

- [ ] Add SMTP environment variables
- [ ] Test email sending (submit test feedback)
- [ ] Verify owner receives notification email
- [ ] Verify user receives confirmation email
- [ ] Add feedback form to dashboard UI
- [ ] Add "Send Feedback" button to header/menu
- [ ] Document feedback process for users
- [ ] Create support page with contact info
- [ ] Set SLA for response time (24 hours recommended)
- [ ] Monitor /api/feedback/stats/summary regularly

---

## 🚀 Deployment

```bash
# 1. Update .env.production with SMTP settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
OWNER_EMAIL=you@example.com

# 2. Redeploy to Railway
# (automatically uses new env variables)

# 3. Test
curl -X POST https://api.tryclariq.com/api/feedback/submit \
  -H "Content-Type: application/json" \
  -d '{
    "user_email": "test@example.com",
    "subject": "Test feedback",
    "message": "This is a test feedback message"
  }'

# 4. Check /api/support/status
curl https://api.tryclariq.com/api/support/status
```

---

## 📈 Monitoring

**Track in dashboard:**
- Total feedback count (should be healthy if 1-2/week)
- Open feedback (should stay <5)
- Bug vs feature split
- Response time (aim for <24 hours)

**Alert on:**
- Surge in "bug" reports (potential issue)
- "Urgent" feedback (respond immediately)
- Complaints (needs investigation)

---

Now you have a complete feedback system! Users can report issues and you'll get email notifications. 📬✅
