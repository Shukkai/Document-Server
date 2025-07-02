"""
Session management for Document Server CLI
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import requests
from rich.console import Console

console = Console()


class SessionManager:
    """Manages terminal-based sessions for the CLI"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv('DOCUMENT_SERVER_URL', 'http://localhost:5001')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DocumentServerCLI/1.0'
        })
        
        # Generate unique session ID for this terminal
        self.session_id = self._generate_session_id()
        
        # Auto-load the session for this terminal
        self._load_terminal_session()
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID for this terminal"""
        terminal_id = os.getenv('TERM_SESSION_ID', '')
        process_id = str(os.getpid())
        cwd = str(Path.cwd())
        
        session_data = f"{terminal_id}_{process_id}_{cwd}"
        return hashlib.md5(session_data.encode()).hexdigest()[:8]
    
    def _load_terminal_session(self):
        """Load session for this specific terminal"""
        session_file = self._get_terminal_session_file()
        if session_file.exists():
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                    self.session.cookies.update(session_data.get('cookies', {}))
                return True
            except:
                pass
        return False
    
    def _save_terminal_session(self, username: str):
        """Save session for this specific terminal"""
        try:
            session_file = self._get_terminal_session_file()
            session_data = {
                'cookies': dict(self.session.cookies),
                'username': username,
                'session_id': self.session_id,
                'terminal_id': os.getenv('TERM_SESSION_ID', ''),
                'process_id': os.getpid(),
                'timestamp': datetime.now().isoformat()
            }
            with open(session_file, 'w') as f:
                json.dump(session_data, f)
        except:
            pass
    
    def _get_terminal_session_file(self) -> Path:
        """Get session file path for this terminal"""
        cli_dir = Path.cwd() / 'cli'
        sessions_dir = cli_dir / 'sessions'
        sessions_dir.mkdir(parents=True, exist_ok=True)
        return sessions_dir / f'terminal_{self.session_id}.session'
    
    def _clear_session(self):
        """Clear current session"""
        self.session.cookies.clear()
    
    def login(self, username: str, password: str) -> bool:
        """Login to the Document Server backend"""
        try:
            self._clear_session()
            
            response = self._make_request('POST', '/login', json={
                'username': username,
                'password': password
            })
            
            if response and response.get('message') == 'Login successful':
                user_info = response.get('user', {})
                console.print(f"[green]Login successful! Welcome, {user_info.get('username', 'User')}[/green]")
                console.print(f"[blue]Terminal Session ID: {self.session_id}[/blue]")
                self._save_terminal_session(username)
                return True
            else:
                error_msg = response.get('error', 'Login failed') if response else 'Login failed'
                console.print(f"[red]Login failed: {error_msg}[/red]")
                return False
        except Exception as e:
            console.print(f"[red]Login failed: {e}[/red]")
            return False
    
    def register(self, username: str, email: str, password: str, grade: int = 33) -> bool:
        """Register a new user account"""
        if not username or not username.strip():
            console.print("[red]Username cannot be empty[/red]")
            return False
        
        if not email or not email.strip():
            console.print("[red]Email cannot be empty[/red]")
            return False
        
        if not password or not password.strip():
            console.print("[red]Password cannot be empty[/red]")
            return False
        
        if len(password) < 1:
            console.print("[red]Password must be at least 1 character long[/red]")
            return False
        
        if '@' not in email or '.' not in email:
            console.print("[red]Please provide a valid email address[/red]")
            return False
        
        try:
            response = self._make_request('POST', '/register', json={
                'username': username.strip(),
                'email': email.strip(),
                'password': password,
                'grade': grade
            })
            
            if response and response.get('message') == 'Registered successfully.':
                console.print(f"[green]Registration successful! Please login, {username}[/green]")
                return True
            else:
                error_msg = response.get('message', 'Registration failed') if response else 'Registration failed'
                console.print(f"[red]Registration failed: {error_msg}[/red]")
                if error_msg == "User already exists":
                    console.print("[yellow]Try using a different username or email address.[/yellow]")
                elif error_msg == "Username, email, and password are required":
                    console.print("[yellow]Please provide all required fields: username, email, and password.[/yellow]")
                return False
        except Exception as e:
            console.print(f"[red]Registration failed: {e}[/red]")
            return False
    
    def logout(self) -> bool:
        """Logout from the Document Server backend"""
        try:
            user_info = self.get_current_user()
            username = user_info.get('username') if user_info else None
            
            self._make_request('POST', '/logout')
            self._clear_session()
            
            session_file = self._get_terminal_session_file()
            if session_file.exists():
                try:
                    session_file.unlink()
                except:
                    pass
            
            console.print("[green]Logged out successfully![/green]")
            console.print("[blue]Current directory reset to root[/blue]")
            return True
        except Exception as e:
            console.print(f"[red]Logout failed: {e}[/red]")
            return False
    
    def is_session_valid(self) -> bool:
        """Check if the current session is still valid"""
        if not self.session.cookies:
            self._load_terminal_session()
        
        try:
            response = self._make_request('GET', '/session-status')
            return response is not None and response.get('authenticated') == True
        except:
            return False
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current user information"""
        try:
            response = self._make_request('GET', '/session-status')
            if response and response.get('authenticated'):
                user_data = response.get('user', {})
                return {
                    'username': user_data.get('username'),
                    'email': user_data.get('email'),
                    'role': 'Administrator' if user_data.get('is_admin') else 'User'
                }
            return None
        except:
            return None
    
    def show_login_status(self):
        """Show current login status"""
        if not self.is_session_valid():
            console.print("[yellow]No active session in this terminal. Please login first.[/yellow]")
            return
        
        user_info = self.get_current_user()
        if user_info:
            console.print(f"[green]Currently logged in as: {user_info['username']} ({user_info['email']})[/green]")
            console.print(f"[blue]Role: {user_info['role']}[/blue]")
            console.print(f"[cyan]Terminal Session ID: {self.session_id}[/cyan]")
        else:
            console.print("[yellow]Please login first[/yellow]")
    
    def list_sessions(self) -> list:
        """List all available terminal sessions"""
        cli_dir = Path.cwd() / 'cli'
        sessions_dir = cli_dir / 'sessions'
        if not sessions_dir.exists():
            return []
        
        sessions = []
        for session_file in sessions_dir.glob('terminal_*.session'):
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                    username = session_data.get('username', 'Unknown')
                    timestamp = session_data.get('timestamp', 'Unknown')
                    session_id = session_data.get('session_id', 'Unknown')
                    process_id = session_data.get('process_id', 'Unknown')
                    sessions.append({
                        'username': username,
                        'timestamp': timestamp,
                        'session_id': session_id,
                        'process_id': process_id,
                        'file': session_file
                    })
            except:
                pass
        
        return sessions
    
    def switch_user(self, username: str) -> bool:
        """Switch to a different user session (not applicable in terminal-based sessions)"""
        console.print("[yellow]User switching is not available in terminal-based sessions.[/yellow]")
        console.print("[yellow]Each terminal maintains its own independent session.[/yellow]")
        console.print("[yellow]To use a different user, login in a new terminal window.[/yellow]")
        return False
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to the backend"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            from rich.progress import Progress, SpinnerColumn, TextColumn
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("Making request...", total=None)
                response = self.session.request(method, url, **kwargs)
                progress.update(task, completed=True)
            
            if response.status_code == 401:
                console.print("[red]Authentication required. Please login first.[/red]")
                return None
            
            response.raise_for_status()
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            console.print(f"[red]Request failed: {e}[/red]")
            return None 