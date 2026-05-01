from locust import HttpUser, task, between
import random

class SavingsMonopolyUser(HttpUser):
    """
    Simulates a real user playing through Savings Monopoly.
    Each simulated user follows a realistic flow:
    - Load the app
    - Set up a player
    - Draw cards and make decisions across multiple rounds
    """
    wait_time = between(2, 6)  # realistic think time between actions (seconds)

    def on_start(self):
        """Called once when each simulated user starts."""
        self.round = 0
        self.total_rounds = 10
        self._load_app()

    def _load_app(self):
        """Simulate loading the setup page."""
        with self.client.get(
            "/",
            catch_response=True,
            name="1. Load setup page"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Setup page failed: {response.status_code}")

    @task(1)
    def simulate_setup(self):
        """Simulate a user filling in the setup form."""
        with self.client.get(
            "/",
            catch_response=True,
            name="2. Player setup"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Setup failed: {response.status_code}")

    @task(5)
    def simulate_game_round(self):
        """
        Simulate a user playing a round on the game page.
        This is weighted 5x higher than setup since most time is spent here.
        """
        with self.client.get(
            "/game",
            catch_response=True,
            name="3. Game page - draw card"
        ) as response:
            if response.status_code == 200:
                response.success()
                self.round += 1
            else:
                response.failure(f"Game page failed: {response.status_code}")

    @task(5)
    def simulate_decision(self):
        """Simulate a user making a decision after drawing a card."""
        # Simulate the think time a user takes to read the card and decide
        think_time = random.uniform(3, 10)

        with self.client.get(
            "/game",
            catch_response=True,
            name="4. Game page - save decision"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Decision save failed: {response.status_code}")

    @task(1)
    def simulate_idle(self):
        """
        Simulate a user sitting idle (reading a card, thinking).
        This keeps the WebSocket connection alive without sending requests,
        mimicking real user behaviour.
        """
        self.client.get(
            "/game",
            name="5. Game page - idle"
        )


class LightUser(HttpUser):
    """
    Simulates a lighter user who just loaded the app and is reading/idle.
    Represents participants who are slower or less engaged.
    """
    wait_time = between(5, 15)

    @task
    def just_browsing(self):
        with self.client.get(
            "/",
            catch_response=True,
            name="Light user - setup page"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")

    @task(3)
    def reading_game(self):
        with self.client.get(
            "/game",
            catch_response=True,
            name="Light user - game page"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")