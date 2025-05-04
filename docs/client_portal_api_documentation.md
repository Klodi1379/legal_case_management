# Client Portal API Documentation

## Overview

This document provides technical information about the Client Portal API and integration points. The API allows for programmatic access to client portal data and functionality, enabling integrations with other systems.

## Authentication

All API requests require authentication using JWT (JSON Web Tokens).

### Obtaining a Token

```
POST /api/token/
```

**Request Body:**
```json
{
  "username": "client_username",
  "password": "client_password"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Using the Token

Include the access token in the Authorization header for all API requests:

```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Refreshing a Token

```
POST /api/token/refresh/
```

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## API Endpoints

### Client Information

#### Get Client Profile

```
GET /api/portal/profile/
```

**Response:**
```json
{
  "id": 1,
  "user": {
    "id": 5,
    "username": "client_username",
    "email": "client@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "company_name": "Acme Inc.",
  "phone": "123-456-7890",
  "address": "123 Main St, Anytown, USA"
}
```

### Cases

#### List Client Cases

```
GET /api/portal/cases/
```

**Response:**
```json
[
  {
    "id": 1,
    "title": "Contract Dispute",
    "case_number": "CD-2023-001",
    "status": "OPEN",
    "open_date": "2023-01-15",
    "description": "Contract dispute with supplier",
    "case_type": "CIVIL"
  },
  {
    "id": 2,
    "title": "Trademark Registration",
    "case_number": "TR-2023-002",
    "status": "OPEN",
    "open_date": "2023-02-20",
    "description": "Trademark registration for new product",
    "case_type": "INTELLECTUAL_PROPERTY"
  }
]
```

#### Get Case Details

```
GET /api/portal/cases/{case_id}/
```

**Response:**
```json
{
  "id": 1,
  "title": "Contract Dispute",
  "case_number": "CD-2023-001",
  "status": "OPEN",
  "open_date": "2023-01-15",
  "description": "Contract dispute with supplier",
  "case_type": "CIVIL",
  "assigned_attorney": {
    "id": 3,
    "name": "Jane Smith",
    "email": "jsmith@example.com"
  },
  "documents": [
    {
      "id": 1,
      "title": "Contract",
      "file_type": "PDF",
      "uploaded_at": "2023-01-16T14:30:00Z"
    }
  ],
  "tasks": [
    {
      "id": 1,
      "title": "Review Contract",
      "status": "PENDING",
      "due_date": "2023-01-30"
    }
  ]
}
```

### Messages

#### List Message Threads

```
GET /api/portal/messages/
```

**Response:**
```json
[
  {
    "id": 1,
    "subject": "Contract Review",
    "case": 1,
    "created_at": "2023-01-17T10:15:00Z",
    "updated_at": "2023-01-18T14:20:00Z",
    "unread_count": 2
  },
  {
    "id": 2,
    "subject": "Document Request",
    "case": 1,
    "created_at": "2023-01-19T09:30:00Z",
    "updated_at": "2023-01-19T09:30:00Z",
    "unread_count": 0
  }
]
```

#### Get Message Thread

```
GET /api/portal/messages/{thread_id}/
```

**Response:**
```json
{
  "id": 1,
  "subject": "Contract Review",
  "case": {
    "id": 1,
    "title": "Contract Dispute"
  },
  "created_at": "2023-01-17T10:15:00Z",
  "updated_at": "2023-01-18T14:20:00Z",
  "messages": [
    {
      "id": 1,
      "sender": {
        "id": 3,
        "name": "Jane Smith"
      },
      "content": "Please review the attached contract",
      "created_at": "2023-01-17T10:15:00Z",
      "is_read": true
    },
    {
      "id": 2,
      "sender": {
        "id": 5,
        "name": "John Doe"
      },
      "content": "I've reviewed the contract and have some questions",
      "created_at": "2023-01-17T15:45:00Z",
      "is_read": true
    }
  ]
}
```

#### Create Message

```
POST /api/portal/messages/{thread_id}/
```

**Request Body:**
```json
{
  "content": "This is my message content"
}
```

**Response:**
```json
{
  "id": 3,
  "sender": {
    "id": 5,
    "name": "John Doe"
  },
  "content": "This is my message content",
  "created_at": "2023-01-20T11:30:00Z",
  "is_read": false
}
```

#### Create Message Thread

```
POST /api/portal/messages/
```

**Request Body:**
```json
{
  "subject": "New Thread Subject",
  "case": 1,
  "message": "Initial message content"
}
```

**Response:**
```json
{
  "id": 3,
  "subject": "New Thread Subject",
  "case": {
    "id": 1,
    "title": "Contract Dispute"
  },
  "created_at": "2023-01-20T11:35:00Z",
  "updated_at": "2023-01-20T11:35:00Z",
  "messages": [
    {
      "id": 4,
      "sender": {
        "id": 5,
        "name": "John Doe"
      },
      "content": "Initial message content",
      "created_at": "2023-01-20T11:35:00Z",
      "is_read": false
    }
  ]
}
```

### Documents

#### List Documents

```
GET /api/portal/documents/
```

**Response:**
```json
[
  {
    "id": 1,
    "title": "Contract",
    "description": "Service agreement",
    "file_type": "PDF",
    "file_size": 1250000,
    "uploaded_at": "2023-01-16T14:30:00Z",
    "case": {
      "id": 1,
      "title": "Contract Dispute"
    }
  },
  {
    "id": 2,
    "title": "Email Correspondence",
    "description": "Emails with supplier",
    "file_type": "PDF",
    "file_size": 850000,
    "uploaded_at": "2023-01-17T09:15:00Z",
    "case": {
      "id": 1,
      "title": "Contract Dispute"
    }
  }
]
```

#### Get Document

```
GET /api/portal/documents/{document_id}/
```

**Response:**
```json
{
  "id": 1,
  "title": "Contract",
  "description": "Service agreement",
  "file_type": "PDF",
  "file_size": 1250000,
  "uploaded_at": "2023-01-16T14:30:00Z",
  "case": {
    "id": 1,
    "title": "Contract Dispute"
  },
  "download_url": "/api/portal/documents/1/download/"
}
```

#### Download Document

```
GET /api/portal/documents/{document_id}/download/
```

**Response:**
Binary file data with appropriate Content-Type header

### Tasks

#### List Tasks

```
GET /api/portal/tasks/
```

**Response:**
```json
[
  {
    "id": 1,
    "title": "Review Contract",
    "description": "Please review the contract and provide feedback",
    "status": "PENDING",
    "due_date": "2023-01-30",
    "case": {
      "id": 1,
      "title": "Contract Dispute"
    }
  },
  {
    "id": 2,
    "title": "Provide Additional Information",
    "description": "Please provide information about previous agreements",
    "status": "IN_PROGRESS",
    "due_date": "2023-02-15",
    "case": {
      "id": 1,
      "title": "Contract Dispute"
    }
  }
]
```

### Notifications

#### List Notifications

```
GET /api/portal/notifications/
```

**Response:**
```json
[
  {
    "id": 1,
    "notification_type": "MESSAGE",
    "title": "New message in: Contract Review",
    "message": "Jane Smith sent a new message in Contract Review",
    "created_at": "2023-01-18T14:20:00Z",
    "is_read": false,
    "related_object_type": "MessageThread",
    "related_object_id": 1
  },
  {
    "id": 2,
    "notification_type": "DOCUMENT",
    "title": "New document uploaded",
    "message": "A new document 'Email Correspondence' has been uploaded to your case",
    "created_at": "2023-01-17T09:15:00Z",
    "is_read": true,
    "related_object_type": "Document",
    "related_object_id": 2
  }
]
```

#### Mark Notification as Read

```
POST /api/portal/notifications/{notification_id}/read/
```

**Response:**
```json
{
  "id": 1,
  "notification_type": "MESSAGE",
  "title": "New message in: Contract Review",
  "message": "Jane Smith sent a new message in Contract Review",
  "created_at": "2023-01-18T14:20:00Z",
  "is_read": true,
  "related_object_type": "MessageThread",
  "related_object_id": 1
}
```

## Webhooks

The Client Portal can send webhook notifications for various events. To set up webhooks, contact the system administrator.

### Available Webhook Events

- `message.created`: Triggered when a new message is created
- `document.uploaded`: Triggered when a new document is uploaded
- `task.assigned`: Triggered when a task is assigned to a client
- `case.updated`: Triggered when a case is updated

### Webhook Payload Example

```json
{
  "event": "message.created",
  "timestamp": "2023-01-20T11:30:00Z",
  "data": {
    "message_id": 3,
    "thread_id": 1,
    "sender_id": 5,
    "case_id": 1
  }
}
```

## Error Handling

The API uses standard HTTP status codes to indicate the success or failure of requests.

### Common Error Codes

- `400 Bad Request`: The request was invalid
- `401 Unauthorized`: Authentication failed
- `403 Forbidden`: The authenticated user doesn't have permission
- `404 Not Found`: The requested resource doesn't exist
- `500 Internal Server Error`: An error occurred on the server

### Error Response Format

```json
{
  "error": {
    "code": "invalid_request",
    "message": "The request was invalid",
    "details": {
      "field_name": ["Error details"]
    }
  }
}
```

## Rate Limiting

API requests are subject to rate limiting to prevent abuse. The current limits are:

- 100 requests per minute per user
- 1000 requests per hour per user

Rate limit information is included in the response headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1611149700
```

## Integration Examples

### Python Example

```python
import requests
import json

# Authentication
auth_url = "https://example.com/api/token/"
auth_data = {
    "username": "client_username",
    "password": "client_password"
}
auth_response = requests.post(auth_url, json=auth_data)
token = auth_response.json()["access"]

# Get cases
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
cases_url = "https://example.com/api/portal/cases/"
cases_response = requests.get(cases_url, headers=headers)
cases = cases_response.json()

# Send a message
thread_id = 1
message_url = f"https://example.com/api/portal/messages/{thread_id}/"
message_data = {
    "content": "This is a message sent via the API"
}
message_response = requests.post(message_url, headers=headers, json=message_data)
```

### JavaScript Example

```javascript
// Authentication
async function authenticate() {
  const response = await fetch('https://example.com/api/token/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      username: 'client_username',
      password: 'client_password'
    })
  });
  
  const data = await response.json();
  return data.access;
}

// Get cases
async function getCases(token) {
  const response = await fetch('https://example.com/api/portal/cases/', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}

// Send a message
async function sendMessage(token, threadId, content) {
  const response = await fetch(`https://example.com/api/portal/messages/${threadId}/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      content: content
    })
  });
  
  return await response.json();
}

// Usage
(async () => {
  const token = await authenticate();
  const cases = await getCases(token);
  console.log(cases);
  
  if (cases.length > 0) {
    const threadId = 1;
    const message = await sendMessage(token, threadId, 'This is a message sent via the API');
    console.log(message);
  }
})();
```

## Support

For API support, please contact:

- Email: api-support@example.com
- Phone: (555) 123-4567

## Changelog

### v1.0.0 (2023-01-01)
- Initial API release

### v1.1.0 (2023-03-15)
- Added document upload endpoint
- Improved error handling
- Added rate limiting
