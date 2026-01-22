# Langfuse Analytics Dashboards

This document provides configuration for custom Langfuse dashboards to monitor SparkyAI performance, quality, and usage metrics.

## Dashboard Overview

SparkyAI uses Langfuse for comprehensive observability with the following custom dashboards:

1. **Production Metrics** - Real-time performance monitoring
2. **Response Quality** - MaximAI evaluation scores
3. **Cost Analysis** - Token usage and API costs
4. **User Behavior** - Conversation patterns and intents
5. **Error Tracking** - Failures and circuit breaker events

---

## 1. Production Metrics Dashboard

### Key Metrics

#### Response Time
- **P50 Response Time**: Median response time across all requests
- **P95 Response Time**: 95th percentile (slow requests)
- **P99 Response Time**: 99th percentile (very slow requests)

```sql
-- Query for Langfuse Dashboard
SELECT 
  percentile_cont(0.5) WITHIN GROUP (ORDER BY latency) as p50_latency,
  percentile_cont(0.95) WITHIN GROUP (ORDER BY latency) as p95_latency,
  percentile_cont(0.99) WITHIN GROUP (ORDER BY latency) as p99_latency
FROM traces
WHERE name = 'chat_conversation'
  AND timestamp >= NOW() - INTERVAL '24 hours'
```

#### Throughput
- **Requests per Hour**: Total chat requests processed
- **WebSocket Connections**: Active streaming connections
- **Agent Node Execution**: Time spent in each graph node

```sql
-- Requests per hour
SELECT 
  date_trunc('hour', timestamp) as hour,
  COUNT(*) as requests
FROM traces
WHERE name = 'chat_conversation'
  AND timestamp >= NOW() - INTERVAL '7 days'
GROUP BY hour
ORDER BY hour DESC
```

#### Success Rate
- **Total Requests**: All chat requests
- **Successful Requests**: Completed without errors
- **Failed Requests**: Circuit breaker open or errors
- **Success Rate %**: (Successful / Total) * 100

```sql
-- Success rate
SELECT 
  COUNT(*) as total_requests,
  SUM(CASE WHEN level = 'ERROR' THEN 1 ELSE 0 END) as failed_requests,
  (1 - SUM(CASE WHEN level = 'ERROR' THEN 1 ELSE 0 END)::float / COUNT(*)) * 100 as success_rate
FROM traces
WHERE name = 'chat_conversation'
  AND timestamp >= NOW() - INTERVAL '24 hours'
```

---

## 2. Response Quality Dashboard

### MaximAI Evaluation Scores

Track response quality across multiple dimensions using MaximAI scores:

#### Overall Quality Score
- **Average Quality**: Mean of all evaluation scores
- **Quality Trend**: Quality over time (hourly/daily)
- **Quality Distribution**: Histogram of scores

```sql
-- Average quality score
SELECT 
  AVG(value) as avg_quality_score,
  MIN(value) as min_score,
  MAX(value) as max_score,
  percentile_cont(0.5) WITHIN GROUP (ORDER BY value) as median_score
FROM scores
WHERE name = 'response_quality'
  AND timestamp >= NOW() - INTERVAL '7 days'
```

#### Quality Dimensions
- **Relevance**: How well response addresses query
- **Accuracy**: Factual correctness
- **Helpfulness**: Practical value
- **Tone**: Professional and appropriate
- **Safety**: No harmful content

```sql
-- Quality by dimension (from score comments)
SELECT 
  timestamp::date as date,
  AVG(value) as avg_score,
  COUNT(*) as evaluation_count
FROM scores
WHERE name = 'response_quality'
  AND timestamp >= NOW() - INTERVAL '30 days'
GROUP BY date
ORDER BY date DESC
```

#### Low Quality Alerts
- Responses with quality < 0.6
- Sessions with declining quality
- Intent-specific quality issues

```sql
-- Low quality responses
SELECT 
  s.trace_id,
  s.value as quality_score,
  t.input,
  t.output
FROM scores s
JOIN traces t ON s.trace_id = t.id
WHERE s.name = 'response_quality'
  AND s.value < 0.6
  AND s.timestamp >= NOW() - INTERVAL '7 days'
ORDER BY s.value ASC
LIMIT 50
```

---

## 3. Cost Analysis Dashboard

### Token Usage
- **Total Tokens**: Input + Output tokens
- **Input Tokens**: Prompt + context tokens
- **Output Tokens**: Generated response tokens

```sql
-- Token usage by day
SELECT 
  timestamp::date as date,
  SUM(usage_details->'input_tokens') as input_tokens,
  SUM(usage_details->'output_tokens') as output_tokens,
  SUM(usage_details->'total_tokens') as total_tokens
FROM generations
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY date
ORDER BY date DESC
```

### Cost Tracking
- **Daily Cost**: Estimated cost per day
- **Monthly Projection**: Projected monthly cost
- **Cost per Conversation**: Average cost per session

```sql
-- Cost analysis
SELECT 
  timestamp::date as date,
  COUNT(DISTINCT trace_id) as conversations,
  SUM(calculated_total_cost) as total_cost,
  AVG(calculated_total_cost) as avg_cost_per_request,
  SUM(calculated_total_cost) / COUNT(DISTINCT trace_id) as cost_per_conversation
FROM generations
WHERE model = 'gpt-4o-mini'
  AND timestamp >= NOW() - INTERVAL '30 days'
GROUP BY date
ORDER BY date DESC
```

### Budget Alerts
- **Daily Budget**: Alert if > $2.00/day
- **Monthly Budget**: Alert if projected > $30/month
- **Cost Anomalies**: Sudden spikes in usage

---

## 4. User Behavior Dashboard

### Conversation Analytics

#### Intent Distribution
- **Greeting**: Welcome messages
- **Technical**: Skills and experience questions
- **Project**: Project-related questions
- **General**: Other queries

```sql
-- Intent distribution
SELECT 
  metadata->>'intent' as intent,
  COUNT(*) as count,
  AVG(latency) as avg_latency
FROM traces
WHERE name = 'chat_conversation'
  AND timestamp >= NOW() - INTERVAL '7 days'
GROUP BY intent
ORDER BY count DESC
```

#### Session Metrics
- **Average Session Length**: Messages per session
- **Session Duration**: Time from first to last message
- **Bounce Rate**: Sessions with only 1 message

```sql
-- Session metrics
WITH session_stats AS (
  SELECT 
    session_id,
    COUNT(*) as message_count,
    MAX(timestamp) - MIN(timestamp) as duration
  FROM traces
  WHERE name = 'chat_conversation'
    AND timestamp >= NOW() - INTERVAL '7 days'
  GROUP BY session_id
)
SELECT 
  AVG(message_count) as avg_messages_per_session,
  AVG(EXTRACT(EPOCH FROM duration)) as avg_duration_seconds,
  SUM(CASE WHEN message_count = 1 THEN 1 ELSE 0 END)::float / COUNT(*) * 100 as bounce_rate_pct
FROM session_stats
```

#### Popular Questions
- **Most Asked**: Top 20 most common questions
- **Unanswered**: Questions with low retrieval confidence
- **Trending**: Questions increasing in frequency

```sql
-- Most asked questions
SELECT 
  input as question,
  COUNT(*) as frequency,
  AVG(metadata->>'retrieval_confidence') as avg_confidence
FROM traces
WHERE name = 'chat_conversation'
  AND timestamp >= NOW() - INTERVAL '7 days'
GROUP BY input
ORDER BY frequency DESC
LIMIT 20
```

---

## 5. Error Tracking Dashboard

### Error Rates

#### Error by Type
- **Circuit Breaker Open**: OpenAI service unavailable
- **Rate Limit Exceeded**: Too many requests
- **Invalid Input**: Prompt injection detected
- **Internal Error**: Unexpected failures

```sql
-- Error distribution
SELECT 
  level as error_level,
  COUNT(*) as error_count,
  COUNT(*)::float / (SELECT COUNT(*) FROM traces WHERE timestamp >= NOW() - INTERVAL '24 hours') * 100 as error_rate_pct
FROM traces
WHERE level = 'ERROR'
  AND timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY level
```

#### Circuit Breaker Status
- **State Changes**: CLOSED → OPEN → HALF_OPEN
- **Failure Rate**: Failures leading to open circuit
- **Recovery Time**: Time to close circuit

```sql
-- Circuit breaker events
SELECT 
  timestamp,
  metadata->>'circuit_state' as state,
  metadata->>'failure_count' as failures
FROM observations
WHERE name = 'circuit_breaker_state_change'
  AND timestamp >= NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC
```

#### Recent Errors
- **Last 100 Errors**: Recent error messages
- **Error Patterns**: Recurring error types
- **Affected Users**: Sessions with errors

```sql
-- Recent errors with context
SELECT 
  timestamp,
  session_id,
  input,
  output,
  status_message
FROM traces
WHERE level = 'ERROR'
  AND timestamp >= NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC
LIMIT 100
```

---

## Dashboard Setup Instructions

### 1. Access Langfuse Dashboards

1. Go to [Langfuse Cloud](https://cloud.langfuse.com)
2. Navigate to your project
3. Click "Dashboards" in the sidebar
4. Click "Create Dashboard"

### 2. Create Custom Dashboard

1. **Name**: e.g., "SparkyAI Production Metrics"
2. **Add Widgets**:
   - Click "Add Widget"
   - Select widget type (Chart, Table, Number)
   - Paste SQL query from above
   - Configure visualization options

### 3. Widget Types

#### Number Widget
- Single metric display
- Good for: Success rate, total requests, avg quality

#### Line Chart
- Time series data
- Good for: Trends, throughput, costs over time

#### Bar Chart
- Categorical comparisons
- Good for: Intent distribution, error types

#### Table
- Detailed data
- Good for: Recent errors, low quality responses

### 4. Refresh Settings

- **Auto-refresh**: Set to 1 minute for real-time monitoring
- **Time Range**: Last 24 hours for production metrics
- **Filters**: Add filters for session_id, intent, date range

---

## Alert Configuration

### Critical Alerts

1. **High Error Rate**
   - Condition: Error rate > 5% in last hour
   - Action: Notify on-call engineer

2. **Circuit Breaker Open**
   - Condition: Circuit state = OPEN
   - Action: Immediate notification

3. **Budget Exceeded**
   - Condition: Daily cost > $2.00
   - Action: Disable API, notify admin

4. **Low Quality Responses**
   - Condition: Avg quality < 0.7 for 1 hour
   - Action: Review and retrain

### Warning Alerts

1. **Slow Responses**
   - Condition: P95 latency > 5 seconds
   - Action: Investigate performance

2. **High Token Usage**
   - Condition: Avg tokens > 10,000 per request
   - Action: Review conversation truncation

3. **Increasing Errors**
   - Condition: Error rate increasing trend
   - Action: Monitor closely

---

## Maintenance

### Weekly Review
- Review quality scores for declining trends
- Check cost projections
- Analyze popular questions for knowledge gaps

### Monthly Review
- Update dashboard queries as needed
- Add new metrics based on learnings
- Archive old traces (>90 days)

---

## Example Dashboard Layout

```
┌─────────────────────────────────────────────────────────┐
│  SparkyAI Production Dashboard                          │
├─────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│  │ 1,234   │  │ 98.5%   │  │ 234ms   │  │ $0.45   │   │
│  │Requests │  │Success  │  │P95 Time │  │Cost     │   │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Response Time Trend (24h)           [Line]    │   │
│  │  ▁▂▃▄▃▂▁▂▃▄▅▆▅▄▃▂▁▂▃▄▃▂▁             │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌────────────────────┐  ┌────────────────────────┐   │
│  │ Intent Distribution│  │  Quality Score (7d)    │   │
│  │ ███ Technical 45% │  │  0.87 Avg              │   │
│  │ ██  Project   30% │  │  ████████████░░░       │   │
│  │ █   Greeting  25% │  │  Min: 0.65  Max: 0.98  │   │
│  └────────────────────┘  └────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

**Last Updated**: 2026-01-22
