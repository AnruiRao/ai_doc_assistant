
class AssistantBaseError(Exception):
    status_code = 500

class ConfigurationError(AssistantBaseError):
    status_code = 500

class LLMError(AssistantBaseError):
    status_code = 500

class LLMConnectionError(LLMError):
    status_code = 503

class LLMRateLimitError(LLMError):
    status_code = 429

class LLMTimeoutError(LLMError):
    status_code = 504

class LLMApiError(LLMError):
    status_code = 502

class AgentError(AssistantBaseError):
    status_code = 500

class RetrievalError(AssistantBaseError):
    status_code = 500

class DocumentError(AssistantBaseError):
    status_code = 400