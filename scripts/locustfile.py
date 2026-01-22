"""
Load Testing for SparkyAI with Locust
======================================

This script simulates realistic user traffic to test the performance
and scalability of the SparkyAI API.

Usage:
    # Install locust
    pip install locust

    # Run load test
    locust -f scripts/locustfile.py --host=http://localhost:8000

    # Then open http://localhost:8089 to configure and start the test

Production Testing:
    locust -f scripts/locustfile.py --host=https://api.sparky-ai.dev \
           --users 100 --spawn-rate 10 --run-time 5m --headless
"""

import json
import uuid
from locust import HttpUser, task, between, TaskSet, constant_pacing
from locust.exception import RescheduleTask


class ChatBehavior(TaskSet):
    """Simulates typical user chat interactions."""

    def on_start(self):
        """Initialize session when user starts."""
        self.session_id = str(uuid.uuid4())
        self.message_count = 0
        self.queries = [
            "What are your skills?",
            "Tell me about your experience with Python",
            "What projects have you worked on?",
            "Do you have experience with machine learning?",
            "What's your background in web development?",
            "Can you tell me about your education?",
            "What technologies do you know?",
            "Have you worked with React?",
            "Tell me about your AI projects",
            "What are your strengths?",
        ]

    @task(5)
    def send_chat_message(self):
        """Send a chat message (most common action)."""
        if self.message_count >= 10:
            # Reset after 10 messages to simulate new conversation
            self.session_id = str(uuid.uuid4())
            self.message_count = 0

        # Select a query
        query = self.queries[self.message_count % len(self.queries)]
        self.message_count += 1

        # Send chat request
        with self.client.post(
            "/chat",
            json={
                "message": query,
                "session_id": self.session_id,
            },
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                # Rate limited - expected behavior
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(2)
    def get_embeddings(self):
        """Get embedding visualization data."""
        with self.client.get("/embeddings", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to get embeddings: {response.status_code}")

    @task(1)
    def get_graph_structure(self):
        """Get graph structure (less frequent)."""
        with self.client.get("/graph", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if "nodes" in data and "edges" in data:
                    response.success()
                else:
                    response.failure("Invalid graph structure")
            else:
                response.failure(f"Failed to get graph: {response.status_code}")

    @task(10)
    def health_check(self):
        """Health check endpoint (very frequent monitoring)."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")


class QuickVisitor(HttpUser):
    """
    Simulates a quick visitor who checks the site and maybe asks 1-2 questions.
    
    - Wait 1-3 seconds between actions
    - Lightweight load
    """

    wait_time = between(1, 3)
    weight = 3  # More common user type
    tasks = [ChatBehavior]


class ActiveUser(HttpUser):
    """
    Simulates an engaged user having a longer conversation.
    
    - Wait 2-5 seconds between actions (reading responses)
    - More realistic load
    """

    wait_time = between(2, 5)
    weight = 2
    tasks = [ChatBehavior]


class BotTraffic(HttpUser):
    """
    Simulates rapid automated requests (crawlers, bots).
    
    - Very short wait time
    - Tests rate limiting
    """

    wait_time = between(0.1, 0.5)
    weight = 1
    tasks = [ChatBehavior]


class HealthMonitor(HttpUser):
    """
    Simulates monitoring services hitting the health endpoint.
    
    - Constant 30-second intervals
    - Minimal load but consistent
    """

    wait_time = constant_pacing(30)
    weight = 1

    @task
    def health_check(self):
        """Check health endpoint."""
        self.client.get("/health")


# Custom load shape for realistic traffic patterns
from locust import LoadTestShape


class StepLoadShape(LoadTestShape):
    """
    Gradually increase load to simulate traffic spikes.
    
    Steps:
    1. 0-60s: Ramp up to 10 users
    2. 60-120s: Maintain 10 users
    3. 120-180s: Spike to 50 users
    4. 180-240s: Drop to 20 users
    5. 240-300s: Back to 10 users
    """

    step_time = 60
    step_load = 10
    spawn_rate = 2

    def tick(self):
        """Define load for each time step."""
        run_time = self.get_run_time()

        if run_time < 60:
            # Ramp up
            user_count = int(run_time / 60 * 10)
            return (user_count, self.spawn_rate)

        elif run_time < 120:
            # Steady state
            return (10, self.spawn_rate)

        elif run_time < 180:
            # Traffic spike
            return (50, 5)

        elif run_time < 240:
            # Cool down
            return (20, 3)

        elif run_time < 300:
            # Return to normal
            return (10, 2)

        else:
            # Stop test
            return None


# Events for custom metrics
from locust import events


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Log when load test starts."""
    print(f"\n{'=' * 60}")
    print(f"🚀 Starting SparkyAI Load Test")
    print(f"   Host: {environment.host}")
    print(f"   Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")
    print(f"{'=' * 60}\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Log test results when stopped."""
    print(f"\n{'=' * 60}")
    print(f"✅ Load Test Complete")
    
    stats = environment.stats
    print(f"\n📊 Summary:")
    print(f"   Total Requests: {stats.total.num_requests}")
    print(f"   Failures: {stats.total.num_failures}")
    print(f"   Avg Response Time: {stats.total.avg_response_time:.2f}ms")
    print(f"   Max Response Time: {stats.total.max_response_time:.2f}ms")
    print(f"   Requests/sec: {stats.total.total_rps:.2f}")
    print(f"{'=' * 60}\n")


# Custom task for WebSocket testing (more advanced)
from locust.contrib.fasthttp import FastHttpUser


class WebSocketUser(FastHttpUser):
    """
    Advanced user that tests WebSocket connections.
    
    Note: Requires gevent-websocket for WebSocket support.
    """

    wait_time = between(2, 5)
    weight = 1

    @task
    def websocket_chat(self):
        """Test WebSocket streaming chat."""
        # Note: This is a placeholder - actual WebSocket testing
        # requires additional setup with gevent-websocket
        pass
