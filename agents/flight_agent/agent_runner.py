from google.adk.runners import Runner

class AgentRunner:
    def __init__(self, agent, session_service, app_name):
        self.agent = agent
        self.session_service = session_service
        self.app_name = app_name

    async def run(self, user_id, session_id, message):
        # Ensure session exists
        self.session_service.create_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id
        )
        runner = Runner(
            agent=self.agent,
            app_name=self.app_name,
            session_service=self.session_service
        )
        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=message):
            yield event
