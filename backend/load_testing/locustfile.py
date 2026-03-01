import random
from locust import HttpUser, task, between

class RiskScoringUser(HttpUser):
    """
    Simulates a concurrent user connecting to the Financial Risk Scoring API.
    Handles JWT authentication precisely once on startup, storing the token for repeatedly
    issuing `POST /predict/{applicant_id}` endpoints.
    """
    
    # Wait between 1 and 3 seconds between tasks simulating human think time/client delay
    wait_time = between(1.0, 3.0)
    
    def on_start(self):
        """
        Executed exactly once per Locust Virtual User upon start. 
        Mocks a distinct user registration + login to acquire a strict JWT Token.
        """
        # Generate a loosely random email to avoid explicit collisions preventing test runs
        self.user_email = f"loadtest_{random.randint(100000, 9999999)}@test.com"
        self.password = "secure_password"
        
        # 1. Register User Mock
        self.client.post(
            "/auth/register",
            json={
                "email": self.user_email,
                "password": self.password,
                "role": "APPLICANT"
            },
            name="Authenticate - Register User"
        )
        
        # 2. Login User to extract OAuth2 Bearer Token
        response = self.client.post(
            "/auth/login",
            data={
                "username": self.user_email,
                "password": self.password
            },
            name="Authenticate - Login JWT"
        )
        
        if response.status_code == 200:
            token_data = response.json()
            # Construct standard Authorization header for usage
            self.headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        else:
            # Locust will explicitly mark initialization failures 
            response.failure(f"Failed to acquire JWT on Login. Status: {response.status_code}")
            self.environment.runner.quit()

    @task
    def execute_risk_prediction(self):
        """
        Repeatedly hits the heavy CPU-bound predict endpoint. 
        Varies the applicant ID to test realistic distributions versus Redis cache hitting overlaps.
        """
        # Assume a bounded set of users. 
        # Tightly constrain to test Redis caching randomly overlap (e.g. 1-20).
        applicant_id = random.randint(1, 20)
        
        with self.client.post(
            f"/predict/{applicant_id}", 
            headers=getattr(self, "headers", {}),
            catch_response=True,
            name="Predict - High CPU ML Target"
        ) as response:
            
            # Graceful error handling exposing Locust UI tracing
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # 404 logic implies the Random User integer isn't created in the system, 
                # acceptable noise relying on `on_start` to seed enough random integers reliably
                response.failure(f"Application missing underlying Applicant Record via 404")
            else:
                response.failure(f"Generic HTTP Failure executing Predict. Code: {response.status_code}")
