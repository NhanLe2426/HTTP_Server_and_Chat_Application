import functools
import inspect

def require_auth(func):
    """
    Decorator to enforce user authentication.
    Intercepts the incoming request to check for a valid 'session' cookie.
    If unauthorized, returns an error payload without executing the wrapped route handler.
    """
    
    # Handle Asynchronous route handlers (e.g., async def hello)
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            headers = kwargs.get('headers', {})
            # Retrieve cookie string (handling potential case-insensitivity)
            cookie_str = headers.get('cookie', headers.get('Cookie', ''))
            
            # Check if the session token exists in the cookie
            if 'session=' not in cookie_str:
                return {"error": "401 Unauthorized - Access Denied"}
            
            # Valid session found, proceed to the actual route handler
            return await func(*args, **kwargs)
        return async_wrapper
        
    # Handle Synchronous route handlers (e.g., def login)
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            headers = kwargs.get('headers', {})
            cookie_str = headers.get('cookie', headers.get('Cookie', ''))
            
            if 'session=' not in cookie_str:
                return {"error": "401 Unauthorized - Access Denied"}
            
            return func(*args, **kwargs)
        return sync_wrapper