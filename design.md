# Task Prioritizer Design Document

## 1. Problem & Goals

### Problem Statement
Individuals with ADHD struggle with constant task inflow from multiple channels (text, email, Slack, conversations, physical world) leading to:
- Cognitive overhead from manual prioritization
- Forgotten tasks and missed deadlines
- Time wasted on complex productivity systems
- Lack of automatic calendar integration

It's not just tasks though, it's articles, videos, or podcasts to listen to "later" but pushed to the recess of their mind, and ultimately forgotten.

example #1: https://www.reddit.com/r/productivity/comments/1l9jre5/does_anyone_else_feel_like_their_todo_list_is/

The user spends more time learning how to use the to-do list tool, creating complicated systems, and managing their list.

example #2: https://www.reddit.com/r/ticktick/comments/1lanmzs/my_ticktick_setup_in_2025_designed_for_clarity/

### Goals
- Enable instant task capture with automatic structuring and prioritization
- Eliminate manual calendar scheduling through intelligent time-boxing
- Reduce cognitive load by automating task prioritization decisions
- Provide seamless cross-device synchronization

### Success Metrics
- Task completion rate increase >20%
- Time spent on task management reduced by >50%
- User retention >70% after 30 days

## 2. Non-Goals (MVP)
- Multi-user collaboration
- Advanced analytics/reporting
- Integration with project management tools
- Mobile app (web-responsive only)
- Offline functionality
- Custom calendar providers beyond Google Calendar

## 3. User Stories & Requirements

### User Stories
1. P0: As a user, I can input freeform tasks ("email Sarah, finish report, book dentist") to add, delete, and update tasks.
2. P0: As a user, I can access my synchronized task list from any device.
3. P0: As a user, I can input a task and see it automatically time boxed and scheduled on my Google Calendar based on inferred or user-defined priorities.
4. P0: As a user, I can input a task and have it automatically prioritized on my task list based on inferred or user-defined priorities.
5. P0: As a user, I can can modify task priorities and see calendar updates in real-time.
6. P0: As a user, I can reschedule tasks on my calendar from the website and my integrated calendar.

### Functional Requirements
- Parse natural language task input into structured data
- Automatically assign priority scores (1-10) based on urgency, deadlines, and user patterns
- Schedule tasks on Google Calendar with appropriate time blocks
- Handle scheduling conflicts and suggest alternatives
- Real-time synchronization across devices
- Manual override for all automated decisions

### Non-Functional Requirements
- Task input response time <500ms
- LLM processing completion within 30 seconds
- 99.9% data persistence reliability
- Support for 1000+ tasks per user
- Calendar sync latency <5 seconds

## 4. System Design

### Architecture Overview
```
User ↔ React UI ↔ FastAPI ↔ PostgreSQL
                     ↓
                Celery + Redis Queue
                     ↓
                LLM Service
                     ↓
                FastAPI ↔ Google Calendar API
```

### System Flow

#### Task Creation Flow
1. User inputs freeform task text
2. API immediately saves raw task to database (status: "processing")
3. API returns task ID and triggers background job
4. UI shows task in "processing" state
5. Background worker calls LLM to parse and prioritize
6. LLM determines structure, priority, and scheduling
7. System schedules task on Google Calendar
8. Database updated with structured data and reprioritized task list
9. UI receives real-time update via WebSocket

#### Task Modification Flow
1. User modifies task priority or details
2. API updates database immediately
3. Background job triggered for rescheduling
4. Calendar updated accordingly
5. UI reflects changes in real-time

## 5. API Design

### Core Endpoints

```
POST /api/tasks
Body: { "input": "email Sarah about project by 2pm, finish quarterly report" }
Response: { "task_ids": ["uuid1", "uuid2"], "status": "processing" }

GET /api/tasks
Response: { "tasks": [...], "total": 42 }

PUT /api/tasks/{task_id}
Body: { "priority": 8, "scheduled_time": "2025-06-25T14:00:00Z" }

DELETE /api/tasks/{task_id}

POST /api/tasks/{task_id}/reschedule
Body: { "new_time": "2025-06-25T16:00:00Z" }

GET /api/calendar/conflicts
Response: { "conflicts": [...] }
```

### Authentication
- Google OAuth 2.0 for calendar access
- JWT tokens for API authentication

## 6. Database Schema

### Tables

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    google_calendar_token TEXT,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tasks table  
CREATE TABLE tasks (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    raw_input TEXT, -- Original user input
    priority_score INTEGER CHECK (priority_score >= 1 AND priority_score <= 10),
    estimated_duration INTEGER, -- minutes
    due_date TIMESTAMP,
    scheduled_start TIMESTAMP,
    scheduled_end TIMESTAMP,
    calendar_event_id VARCHAR(255), -- Google Calendar event ID
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, scheduled, completed
    metadata JSONB DEFAULT '{}', -- LLM-generated attributes
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Task processing jobs (for debugging/monitoring)
CREATE TABLE task_jobs (
    id UUID PRIMARY KEY,
    task_id UUID REFERENCES tasks(id),
    status VARCHAR(50), -- queued, processing, completed, failed
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);
```

### Indexes
```sql
CREATE INDEX idx_tasks_user_id_status ON tasks(user_id, status);
CREATE INDEX idx_tasks_scheduled_start ON tasks(scheduled_start);
CREATE INDEX idx_tasks_priority_score ON tasks(priority_score);
```

## 7. LLM Integration

### Prompt Design
```
Parse this task input and return structured JSON:
Input: "{user_input}"
Calendar context: {calendar_events}
User preferences: {user_preferences}

Return:
{
  "tasks": [
    {
      "title": "Email Sarah about project",
      "description": "Follow up on quarterly project status",
      "priority_score": 7,
      "estimated_duration": 15,
      "due_date": "2025-06-25T14:00:00Z",
      "suggested_time": "2025-06-25T13:00:00Z"
    }
  ]
}
```

### LLM Service Design
- Separate microservice for LLM calls
- Retry logic with exponential backoff
- Cost monitoring and rate limiting
- Fallback to rule-based parsing if LLM fails

## 8. Implementation Plan

### Phase 1: Core MVP (4 weeks)
- Week 1: Database setup, basic API endpoints
- Week 2: LLM integration and task parsing
- Week 3: Google Calendar integration
- Week 4: Frontend and end-to-end testing

### Phase 2: Polish (2 weeks)  
- Real-time updates via WebSocket
- Error handling and user feedback
- Performance optimization

### Phase 3: Enhancement (ongoing)
- User preference learning
- Advanced scheduling algorithms
- Mobile responsiveness

## 9. Risks & Mitigations

### High-Risk Items
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| LLM API costs exceed budget | High | Medium | Implement caching, rate limiting, fallback rules |
| Google Calendar API rate limits | High | Low | Batch operations, exponential backoff |
| LLM parsing accuracy <80% | Medium | Medium | Extensive prompt engineering, user feedback loop |
| Calendar sync conflicts | Medium | High | Conflict detection algorithm, user notification |

### Technical Risks
- **Data loss**: Implement database backups and transaction logging
- **Performance**: Cache frequent queries, optimize database indexes
- **Security**: Encrypt tokens, implement proper OAuth flow
- **Scalability**: Design for horizontal scaling from day one

## 10. Open Questions

1. How should we handle recurring tasks?
2. What's the optimal retry strategy for failed calendar syncs?
3. Should we store user preference patterns for better LLM prompting?
4. How do we handle timezone differences in scheduling?
5. How do we collect or determine user preferences in the beginning?

## 11. Future Considerations

- Machine learning for personalized priority scoring
- Integration with other calendar providers (Outlook, Apple)
- Voice input for task creation
- Smart notifications and reminders
- Pomodoro timer