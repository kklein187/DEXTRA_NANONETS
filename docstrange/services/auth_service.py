"""
Auth0 authentication service for DocStrange CLI.
"""

import os
import json
import time
import uuid
import hashlib
import base64
import urllib.parse
import webbrowser
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class AuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback from the browser."""
    
    def __init__(self, auth_service, *args, **kwargs):
        self.auth_service = auth_service
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET request from OAuth callback."""
        try:
            # Parse the callback URL
            parsed_url = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            
            if parsed_url.path == '/callback':
                # Extract authorization code or token from callback
                if 'code' in query_params:
                    auth_code = query_params['code'][0]
                    state = query_params.get('state', [None])[0]
                    
                    # Verify state parameter (CSRF protection)
                    if state != self.auth_service.state:
                        self.send_error(400, "Invalid state parameter")
                        return
                    
                    # Exchange code for token
                    success = self.auth_service.exchange_code_for_token(auth_code)
                    
                    if success:
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html')
                        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                        self.send_header('Pragma', 'no-cache')
                        self.send_header('Expires', '0')
                        self.send_header('X-Content-Type-Options', 'nosniff')
                        self.send_header('X-Frame-Options', 'DENY')
                        self.end_headers()
                        
                        html_response = f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <title>DocStrange Authentication</title>
                            <meta charset="utf-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1">
                            <style>
                                body {{ 
                                    font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                                    text-align: center; 
                                    padding: 50px 20px; 
                                    background: linear-gradient(135deg, #f8faff 0%, #eaedff 100%);
                                    margin: 0;
                                    min-height: 100vh;
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                }}
                                .container {{ 
                                    max-width: 500px; 
                                    margin: 0 auto; 
                                    background: white; 
                                    padding: 40px; 
                                    border-radius: 16px; 
                                    box-shadow: 0 8px 32px rgba(84, 111, 255, 0.1);
                                    border: 1px solid rgba(84, 111, 255, 0.1);
                                }}
                                .success {{ 
                                    color: #18855E; 
                                    font-size: 32px; 
                                    margin-bottom: 20px; 
                                    font-weight: 600;
                                }}
                                .title {{
                                    color: #13152A;
                                    font-size: 24px;
                                    font-weight: 600;
                                    margin-bottom: 16px;
                                }}
                                .message {{ 
                                    color: #404558; 
                                    font-size: 16px; 
                                    line-height: 1.6; 
                                    margin-bottom: 24px;
                                }}
                                .close-btn {{ 
                                    background: linear-gradient(135deg, #546FFF 0%, #3A4DB2 100%); 
                                    color: white; 
                                    border: none; 
                                    padding: 12px 28px; 
                                    border-radius: 8px; 
                                    margin-top: 20px; 
                                    cursor: pointer; 
                                    font-size: 14px; 
                                    font-weight: 500;
                                    transition: all 0.2s ease;
                                    box-shadow: 0 4px 12px rgba(84, 111, 255, 0.3);
                                }}
                                .close-btn:hover {{
                                    transform: translateY(-1px);
                                    box-shadow: 0 6px 16px rgba(84, 111, 255, 0.4);
                                }}
                                .logo {{
                                    width: 64px;
                                    height: 64px;
                                    margin: 0 auto 24px;
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                }}
                                .logo img {{
                                    width: 100%;
                                    height: 100%;
                                    object-fit: contain;
                                }}
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <div class="logo">
                                    <img src="https://public-vlms.s3.us-west-2.amazonaws.com/docstrange_logo.svg" alt="DocStrange Logo" />
                                </div>
                                <div class="success">✅</div>
                                <div class="title">Authentication Successful!</div>
                                <div class="message">
                                    You have successfully authenticated with DocStrange CLI.<br>
                                    Your credentials have been securely cached.<br><br>
                                    💡 <strong>You can now close this tab</strong> and return to your terminal.
                                </div>
                                <button class="close-btn" onclick="closeTab()">Close Tab</button>
                            </div>
                            <script>
                                function closeTab() {{
                                    // Try multiple methods to close the tab
                                    try {{
                                        window.close();
                                    }} catch(e) {{
                                        console.log('window.close() failed:', e);
                                    }}
                                    
                                    // If window.close() doesn't work, try to navigate away
                                    try {{
                                        window.location.href = 'about:blank';
                                    }} catch(e) {{
                                        console.log('Navigation failed:', e);
                                    }}
                                    
                                    // Show a message if nothing worked
                                    setTimeout(() => {{
                                        document.body.innerHTML = `
                                            <div style="text-align: center; padding: 40px; font-family: Inter, sans-serif;">
                                                <h2 style="color: #13152A;">✅ Authentication Complete</h2>
                                                <p style="color: #676767;">You can safely close this tab manually.</p>
                                                <p style="color: #676767; font-size: 14px;">Return to your terminal to continue.</p>
                                            </div>
                                        `;
                                    }}, 500);
                                }}
                                
                                // Auto-close after 5 seconds
                                setTimeout(closeTab, 5000);
                                
                                // Also try to close when user clicks anywhere
                                document.addEventListener('click', closeTab);
                            </script>
                        </body>
                        </html>
                        """
                        self.wfile.write(html_response.encode())
                    else:
                        self._send_error_page("Authentication failed")
                        
                elif 'error' in query_params:
                    error = query_params['error'][0]
                    error_description = query_params.get('error_description', [''])[0]
                    self._send_error_page(f"Authentication error: {error}", error_description)
                else:
                    self._send_error_page("Missing authorization code")
            else:
                self.send_error(404, "Not found")
                
        except Exception as e:
            logger.error(f"Error handling callback: {e}")
            self._send_error_page("Internal server error")
    
    def _send_error_page(self, error_message: str, error_description: str = ""):
        """Send a styled error page."""
        self.send_response(400)
        self.send_header('Content-type', 'text/html')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.end_headers()
        
        html_response = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>DocStrange Authentication Error</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ 
                    font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                    text-align: center; 
                    padding: 50px 20px; 
                    background: linear-gradient(135deg, #fff2f2 0%, #ffeded 100%);
                    margin: 0;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .container {{ 
                    max-width: 500px; 
                    margin: 0 auto; 
                    background: white; 
                    padding: 40px; 
                    border-radius: 16px; 
                    box-shadow: 0 8px 32px rgba(208, 43, 43, 0.1);
                    border: 1px solid rgba(208, 43, 43, 0.1);
                }}
                .error {{ 
                    color: #D02B2B; 
                    font-size: 32px; 
                    margin-bottom: 20px; 
                    font-weight: 600;
                }}
                .title {{
                    color: #13152A;
                    font-size: 24px;
                    font-weight: 600;
                    margin-bottom: 16px;
                }}
                .message {{ 
                    color: #404558; 
                    font-size: 16px; 
                    line-height: 1.6; 
                    margin-bottom: 24px;
                }}
                .retry-btn {{ 
                    background: linear-gradient(135deg, #D02B2B 0%, #A82222 100%); 
                    color: white; 
                    border: none; 
                    padding: 12px 28px; 
                    border-radius: 8px; 
                    margin: 10px; 
                    cursor: pointer; 
                    font-size: 14px; 
                    font-weight: 500;
                    text-decoration: none;
                    display: inline-block;
                    transition: all 0.2s ease;
                }}
                .close-btn {{ 
                    background: #676767; 
                    color: white; 
                    border: none; 
                    padding: 12px 28px; 
                    border-radius: 8px; 
                    margin: 10px; 
                    cursor: pointer; 
                    font-size: 14px; 
                    font-weight: 500;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error">❌</div>
                <div class="title">Authentication Failed</div>
                <div class="message">
                    {error_message}<br>
                    {error_description if error_description else 'Please try again or contact support if the issue persists.'}
                </div>
                <button class="close-btn" onclick="window.close()">Close Tab</button>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html_response.encode())
    
    def log_message(self, format, *args):
        """Suppress server logs."""
        pass


class AuthService:
    """Handles browser-based authentication for DocStrange using Auth0."""
    
    def __init__(self, 
                 auth0_domain: str = "nanonets.auth0.com",
                 client_id: str = "meAtfPTIcmqhL7rLi8kCNqmTvdkGch4n",
                 api_base_url: str = "https://docstrange.nanonets.com"):
        self.auth0_domain = auth0_domain
        self.client_id = client_id
        self.api_base_url = api_base_url
        self.cache_dir = Path.home() / ".docstrange"
        self.cache_file = self.cache_dir / "credentials.json"
        self.state = None
        self.code_verifier = None
        self.server = None
        self.server_thread = None
        self.auth_complete = False
        self.auth_success = False
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(exist_ok=True)
    
    def _generate_pkce_params(self) -> tuple[str, str]:
        """Generate PKCE code verifier and challenge."""
        # Generate random code verifier (43-128 characters)
        code_verifier = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')
        
        # Generate code challenge
        challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(challenge).decode('utf-8').rstrip('=')
        
        return code_verifier, code_challenge
    
    def _start_callback_server(self, port: int = 8765) -> str:
        """Start local server to handle OAuth callback with limited ports for Auth0 whitelist."""
        # Limited set of ports for Auth0 whitelist configuration
        ports_to_try = [8765, 8766, 8767, 8768, 8769]  # Exactly 5 ports to whitelist
        
        for try_port in ports_to_try:
            try:
                # Create handler with reference to auth service
                def handler_factory(*args, **kwargs):
                    return AuthCallbackHandler(self, *args, **kwargs)
                
                self.server = HTTPServer(('localhost', try_port), handler_factory)
                actual_port = self.server.server_address[1]
                
                # Start server in background thread
                self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
                self.server_thread.start()
                
                callback_url = f"http://localhost:{actual_port}/callback"
                logger.info(f"Started callback server on {callback_url}")
                return callback_url
                
            except OSError as e:
                if try_port == ports_to_try[-1]:  # Last attempt failed
                    logger.error(f"Failed to start callback server on any of the Auth0-whitelisted ports {ports_to_try}: {e}")
                    print(f"\n❌ Could not start callback server on ports {ports_to_try}")
                    print("💡 Please ensure these ports are available and not blocked by firewall")
                    raise
                else:
                    logger.debug(f"Port {try_port} unavailable, trying next...")
                    continue
            except Exception as e:
                logger.error(f"Failed to start callback server: {e}")
                raise
    
    def _stop_callback_server(self):
        """Stop the callback server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            if self.server_thread:
                self.server_thread.join(timeout=2)
    
    def get_cached_credentials(self) -> Optional[Dict[str, Any]]:
        """Get cached credentials if they exist and are valid."""
        try:
            if not self.cache_file.exists():
                return None
                
            with open(self.cache_file, 'r') as f:
                creds = json.load(f)
            
            # Check if credentials are still valid
            if 'access_token' in creds and 'expires_at' in creds:
                if time.time() < creds['expires_at']:
                    logger.info("Using cached credentials")
                    return creds
                else:
                    logger.info("Cached credentials expired")
                    self.clear_cached_credentials()
            
            return None
            
        except Exception as e:
            logger.error(f"Error reading cached credentials: {e}")
            return None
    
    def cache_credentials(self, credentials: Dict[str, Any]):
        """Cache credentials securely."""
        try:
            # Add expiration time based on expires_in (default 24 hours)
            expires_in = credentials.get('expires_in', 24 * 60 * 60)  # seconds
            credentials['expires_at'] = time.time() + expires_in
            credentials['cached_at'] = time.time()
            
            with open(self.cache_file, 'w') as f:
                json.dump(credentials, f, indent=2)
            
            # Set restrictive permissions (user only)
            os.chmod(self.cache_file, 0o600)
            logger.info("Credentials cached successfully")
            
        except Exception as e:
            logger.error(f"Error caching credentials: {e}")
    
    def clear_cached_credentials(self):
        """Clear cached credentials."""
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
                logger.info("Cached credentials cleared")
        except Exception as e:
            logger.error(f"Error clearing cached credentials: {e}")
    
    def authenticate(self, force_reauth: bool = False) -> Optional[str]:
        """
        Perform browser-based authentication.
        
        Args:
            force_reauth: Force re-authentication even if cached credentials exist
            
        Returns:
            Access token if authentication successful, None otherwise
        """
        # Check for cached credentials first
        if not force_reauth:
            cached_creds = self.get_cached_credentials()
            if cached_creds and 'access_token' in cached_creds:
                return cached_creds['access_token']
        
        try:
            print("\n🔐 DocStrange Authentication")
            print("=" * 50)
            
            # Generate PKCE parameters
            self.code_verifier, code_challenge = self._generate_pkce_params()
            self.state = str(uuid.uuid4())
            
            # Start callback server
            callback_url = self._start_callback_server()
            
            # Build Auth0 authorization URL with Google connection
            auth_params = {
                'response_type': 'code',
                'client_id': self.client_id,
                'redirect_uri': callback_url,
                'scope': 'openid profile email',
                'state': self.state,
                'code_challenge': code_challenge,
                'code_challenge_method': 'S256',
                'connection': 'google-oauth2'  # Force Google login
            }
            
            # Direct Auth0 authorization URL
            auth_url = f"https://{self.auth0_domain}/authorize?{urllib.parse.urlencode(auth_params)}"
            
            print(f"\n🌐 Opening authentication page...")
            print(f"📋 If the browser doesn't open automatically, click this link:")
            print(f"🔗 {auth_url}")
            print(f"\n⏳ Waiting for authentication...")
            print(f"💡 This will timeout in 5 minutes if not completed")
            
            # Open browser
            try:
                webbrowser.open(auth_url)
            except Exception as e:
                logger.warning(f"Could not open browser automatically: {e}")
                print("Please manually open the link above in your browser.")
            
            # Wait for authentication to complete
            timeout = 300  # 5 minutes
            start_time = time.time()
            
            while not self.auth_complete and (time.time() - start_time) < timeout:
                time.sleep(0.5)
            
            # Stop the server
            self._stop_callback_server()
            
            if self.auth_success:
                print("✅ Authentication successful!")
                cached_creds = self.get_cached_credentials()
                print("💾 Credentials cached for secure access")
                return cached_creds.get('access_token') if cached_creds else None
            else:
                if time.time() - start_time >= timeout:
                    print("❌ Authentication timed out after 5 minutes.")
                    print("💡 Try running 'docstrange login' again when ready.")
                else:
                    print("❌ Authentication failed.")
                    print("💡 Please check your internet connection and try again.")
                return None
                
        except KeyboardInterrupt:
            print("\n🛑 Authentication cancelled by user.")
            self._stop_callback_server()
            return None
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            self._stop_callback_server()
            return None
    
    def exchange_code_for_token(self, auth_code: str) -> bool:
        """
        Exchange authorization code for access token directly with Auth0.
        """
        try:
            import requests
            
            # Auth0 token endpoint
            token_endpoint = f"https://{self.auth0_domain}/oauth/token"
            
            # Prepare token exchange data for Auth0
            token_data = {
                'grant_type': 'authorization_code',
                'client_id': self.client_id,
                'code': auth_code,
                'code_verifier': self.code_verifier,
                'redirect_uri': f"http://localhost:{self.server.server_address[1]}/callback"
            }
            
            # Make token exchange request to Auth0
            response = requests.post(
                token_endpoint,
                json=token_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                token_response = response.json()
                
                # Get user info from Auth0
                user_info = self._get_user_info(token_response.get('access_token'))
                
                credentials = {
                    'access_token': token_response.get('access_token'),
                    'refresh_token': token_response.get('refresh_token'),
                    'id_token': token_response.get('id_token'),
                    'token_type': token_response.get('token_type', 'Bearer'),
                    'scope': token_response.get('scope', 'openid profile email'),
                    'expires_in': token_response.get('expires_in', 86400),  # Usually 24 hours
                    'user_email': user_info.get('email'),
                    'user_name': user_info.get('name'),
                    'user_picture': user_info.get('picture'),
                    'auth0_user_id': user_info.get('sub'),
                    'auth0_direct': True
                }
                
                # Cache the credentials
                self.cache_credentials(credentials)
                
                self.auth_complete = True
                self.auth_success = True
                return True
            else:
                logger.error(f"Auth0 token exchange failed: {response.status_code} {response.text}")
                self.auth_complete = True
                self.auth_success = False
                return False
            
        except ImportError:
            logger.error("requests library is required for authentication")
            self.auth_complete = True
            self.auth_success = False
            return False
        except Exception as e:
            logger.error(f"Auth0 token exchange failed: {e}")
            self.auth_complete = True
            self.auth_success = False
            return False
    
    def _get_user_info(self, access_token: str) -> dict:
        """Get user information from Auth0 userinfo endpoint."""
        try:
            import requests
            
            userinfo_endpoint = f"https://{self.auth0_domain}/userinfo"
            
            response = requests.get(
                userinfo_endpoint,
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to get user info: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.warning(f"Error getting user info: {e}")
            return {}
    

    
    def get_access_token(self, force_reauth: bool = False) -> Optional[str]:
        """
        Get access token, performing authentication if necessary.
        
        Args:
            force_reauth: Force re-authentication
            
        Returns:
            Access token if available, None otherwise
        """
        # First check environment variable
        env_key = os.environ.get('NANONETS_API_KEY')
        if env_key and not force_reauth:
            return env_key
        
        # Then check cached credentials or authenticate
        return self.authenticate(force_reauth)

    def refresh_token(self) -> Optional[str]:
        """Refresh access token using refresh token directly with Auth0."""
        try:
            cached_creds = self.get_cached_credentials()
            if not cached_creds or 'refresh_token' not in cached_creds:
                return None
            
            import requests
            
            # Auth0 token refresh endpoint
            refresh_endpoint = f"https://{self.auth0_domain}/oauth/token"
            
            refresh_data = {
                'grant_type': 'refresh_token',
                'client_id': self.client_id,
                'refresh_token': cached_creds['refresh_token']
            }
            
            response = requests.post(
                refresh_endpoint,
                json=refresh_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                
                # Update cached credentials
                cached_creds.update({
                    'access_token': token_data.get('access_token'),
                    'refresh_token': token_data.get('refresh_token', cached_creds['refresh_token']),
                    'id_token': token_data.get('id_token', cached_creds.get('id_token')),
                    'expires_in': token_data.get('expires_in', 86400),
                    'refreshed_at': time.time()
                })
                
                self.cache_credentials(cached_creds)
                logger.info("Auth0 token refreshed successfully")
                return cached_creds['access_token']
            else:
                logger.warning(f"Auth0 token refresh failed: {response.status_code}")
            
        except Exception as e:
            logger.error(f"Auth0 token refresh failed: {e}")
        
        return None


def get_authenticated_token(force_reauth: bool = False) -> Optional[str]:
    """
    Convenience function to get an authenticated access token.
    
    Args:
        force_reauth: Force re-authentication even if cached credentials exist
        
    Returns:
        Access token if authentication successful, None otherwise
    """
    auth_service = AuthService()
    return auth_service.get_access_token(force_reauth)


def clear_auth():
    """Clear cached authentication credentials."""
    auth_service = AuthService()
    auth_service.clear_cached_credentials()


# CLI command for authentication
def main():
    """CLI entry point for authentication."""
    import argparse
    
    parser = argparse.ArgumentParser(description="DocStrange Authentication")
    parser.add_argument('--reauth', action='store_true', 
                       help='Force re-authentication even if cached credentials exist')
    parser.add_argument('--clear', action='store_true',
                       help='Clear cached credentials')
    
    args = parser.parse_args()
    
    auth_service = AuthService()
    
    if args.clear:
        auth_service.clear_cached_credentials()
        print("✅ Cached credentials cleared.")
        return
    
    token = auth_service.get_access_token(force_reauth=args.reauth)
    
    if token:
        print(f"✅ Authentication successful!")
        print(f"🔑 Access Token: {token[:12]}...{token[-4:]}")
        print(f"💾 Credentials cached securely")
    else:
        print("❌ Authentication failed.")


if __name__ == '__main__':
    main()