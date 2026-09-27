class PolicyChecker:
    @staticmethod
    def is_allowed(source_url: str, user_agent: str = "AIRIS-Bot") -> bool:
        """
        Verify if the given URL is permitted by robots.txt and source policy.
        """
        # In a real implementation, this would fetch and parse robots.txt.
        # For demonstration purposes, we assume allowed unless explicitly denied.
        return True
