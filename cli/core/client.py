"""
Document Server CLI Client
"""

import os
import json
import signal
import mimetypes
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from datetime import datetime

console = Console()


class DocumentServerCLI:
    """Client for interacting with Document Server backend"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv('DOCUMENT_SERVER_URL', 'http://localhost:5001')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DocumentServerCLI/1.0'
        })
        
        # Generate unique session ID for this terminal
        self.session_id = self._generate_session_id()
        
        # Current directory tracking
        self.current_folder_id = None
        self.current_folder_name = None
        
        # Auto-load the session for this terminal
        self._load_terminal_session()
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID for this terminal"""
        # Use combination of process ID, terminal ID, and current working directory
        terminal_id = os.getenv('TERM_SESSION_ID', '')
        process_id = str(os.getpid())
        cwd = str(Path.cwd())
        
        # Create a hash of the terminal-specific information
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
    
    def _auto_load_session(self):
        """Automatically load the session for this terminal"""
        self._load_terminal_session()
    

    
    def _clear_session(self):
        """Clear current session"""
        self.session.cookies.clear()
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to the backend"""
        url = f"{self.base_url}{endpoint}"
        
        try:
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
    
    def login(self, username: str, password: str) -> bool:
        """Login to the Document Server backend"""
        try:
            # Clear any existing session
            self._clear_session()
            
            response = self._make_request('POST', '/login', json={
                'username': username,
                'password': password
            })
            
            if response and response.get('message') == 'Login successful':
                user_info = response.get('user', {})
                console.print(f"[green]Login successful! Welcome, {user_info.get('username', 'User')}[/green]")
                console.print(f"[blue]Terminal Session ID: {self.session_id}[/blue]")
                # Save session for this specific terminal
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
        # Validate input
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
        
        # Basic email validation
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
    
    def upload(self, file_path: str) -> bool:
        """Upload a file to the backend"""
        # Check login status first
        if not self.is_session_valid():
            console.print("[yellow]Please login first[/yellow]")
            return False
        
        # Resolve file path with multiple fallback strategies
        original_path = Path(file_path)
        resolved_path = None
        
        # Define search strategies
        search_paths = [
            original_path,  # Strategy 1: Try as provided (absolute or relative to current dir)
            Path.cwd() / original_path,  # Strategy 2: Relative to current working directory
            Path.cwd().parent / original_path,  # Strategy 3: Relative to project root
            Path.home() / original_path,  # Strategy 4: Relative to home directory
            Path.home() / "Downloads" / original_path,  # Strategy 5: In Downloads folder
        ]
        
        # Try each strategy
        for search_path in search_paths:
            if search_path.exists() and search_path.is_file():
                resolved_path = search_path.resolve()
                break
        
        if not resolved_path:
            console.print(f"[red]File not found: {file_path}[/red]")
            console.print("[yellow]Tried the following locations:[/yellow]")
            for i, search_path in enumerate(search_paths, 1):
                console.print(f"  {i}. {search_path}")
            console.print("[yellow]Please provide the full path to the file or ensure it exists in one of these locations.[/yellow]")
            return False
        
        console.print(f"[blue]Uploading file: {resolved_path.name}[/blue]")
        console.print(f"[dim]Full path: {resolved_path}[/dim]")
        
        # Show upload destination
        if self.current_folder_name:
            console.print(f"[blue]Uploading to current directory: {self.current_folder_name}[/blue]")
        else:
            console.print(f"[blue]Uploading to root directory[/blue]")
        
        # Prepare multipart form data
        try:
            # Read file content into memory
            with open(resolved_path, 'rb') as file_obj:
                file_content = file_obj.read()
            
            # Detect MIME type
            mime_type, _ = mimetypes.guess_type(str(resolved_path))
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            # Create file object from memory content
            from io import BytesIO
            files = {'file': (resolved_path.name, BytesIO(file_content), mime_type)}
            
            # Add folder_id to the request if we're in a specific folder
            data = {}
            if self.current_folder_id is not None:
                data['folder_id'] = self.current_folder_id
            
            # Make the request and capture the response for debugging
            url = f"{self.base_url}/upload"
            response = self.session.post(url, files=files, data=data)
            
            if response.status_code == 400:
                console.print(f"[red]Upload failed with 400 error[/red]")
                console.print(f"[red]Response: {response.text}[/red]")
                return False
            
            if response.status_code != 201:
                console.print(f"[red]Upload failed with status {response.status_code}[/red]")
                console.print(f"[red]Response: {response.text}[/red]")
                return False
            
            result = response.json()
            console.print(f"[green]File uploaded successfully! File ID: {result.get('file_id')}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Error uploading file: {e}[/red]")
            return False
    
    def _display_file_list(self, folder: Dict[str, Any]):
        """Display files in a simple list"""
        files = []
        
        def collect_files(folder_dict, folder_path=""):
            current_path = f"{folder_path}/{folder_dict['name']}" if folder_path else folder_dict['name']
            
            for file in folder_dict.get('files', []):
                files.append({
                    'ID': file['id'],
                    'Name': file['name'],
                    'Type': file.get('mimetype', 'Unknown'),
                    'Location': current_path,
                    'Status': 'Under Review' if file.get('is_under_review') else 'Available'
                })
            
            for child in folder_dict.get('children', []):
                collect_files(child, current_path)
        
        collect_files(folder)
        
        if not files:
            console.print("[yellow]No files found[/yellow]")
            return
        
        table = Table(title="Files in Document Server")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="green")
        table.add_column("Type", style="blue")
        table.add_column("Location", style="magenta")
        table.add_column("Status", style="yellow")
        
        for file in files:
            table.add_row(
                str(file['ID']),
                file['Name'],
                file['Type'],
                file['Location'],
                file['Status']
            )
        
        console.print(table)
    
    def get_file_id_by_name(self, filename: str) -> Optional[int]:
        """Find file ID by filename for the current user"""
        try:
            response = self._make_request('GET', '/folders')
            if not response or 'tree' not in response:
                return None
            
            def search_file_in_tree(tree):
                # Search files in current folder
                for file in tree.get('files', []):
                    if file['name'] == filename:
                        return file['id']
                
                # Search in subfolders
                for child in tree.get('children', []):
                    result = search_file_in_tree(child)
                    if result:
                        return result
                
                return None
            
            return search_file_in_tree(response['tree'])
        except Exception as e:
            console.print(f"[red]Error finding file: {e}[/red]")
            return None
    
    def get_file_id_by_name_in_current_dir(self, filename: str) -> Optional[int]:
        """Find file ID by filename, prioritizing current directory"""
        if not self.is_session_valid():
            console.print("[yellow]Please login first[/yellow]")
            return None
        
        try:
            response = self._make_request('GET', '/folders')
            if not response or 'tree' not in response:
                return None
            
            tree = response['tree']
            
            # If we're in a specific folder, search there first
            if self.current_folder_name:
                current_folder = self._find_folder_in_tree(tree, self.current_folder_name)
                if current_folder:
                    # Search in current folder first
                    for file in current_folder.get('files', []):
                        if file['name'] == filename:
                            console.print(f"[blue]Found file '{filename}' in current directory: {self.current_folder_name}[/blue]")
                            return file['id']
            
            # If not found in current directory or we're in root, search entire tree
            def search_file_in_tree(folder_tree):
                # Search files in current folder
                for file in folder_tree.get('files', []):
                    if file['name'] == filename:
                        return file['id']
                
                # Search in subfolders
                for child in folder_tree.get('children', []):
                    result = search_file_in_tree(child)
                    if result:
                        return result
                
                return None
            
            file_id = search_file_in_tree(tree)
            if file_id and self.current_folder_name:
                console.print(f"[blue]Found file '{filename}' in different directory[/blue]")
            return file_id
            
        except Exception as e:
            console.print(f"[red]Error finding file: {e}[/red]")
            return None
    
    def download(self, filename: str, output_path: Optional[str] = None) -> bool:
        """Download a file from the backend by filename"""
        file_id = self.get_file_id_by_name(filename)
        if not file_id:
            console.print(f"[red]File '{filename}' not found.[/red]")
            return False
        # ... rest of the original download method, but use file_id ...
        folders_data = self._make_request('GET', '/folders')
        if not folders_data:
            return False
        file_info = self._find_file_in_tree(folders_data.get('tree', {}), file_id)
        if not file_info:
            console.print(f"[red]File with ID {file_id} not found[/red]")
            return False
        url = f"{self.base_url}/download/{file_id}"
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("Downloading...", total=None)
                response = self.session.get(url, stream=True)
                progress.update(task, completed=True)
            if response.status_code != 200:
                console.print(f"[red]Download failed: {response.text}[/red]")
                return False
            # Determine output path
            if not output_path:
                output_path = file_info['name']
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            console.print(f"[green]File downloaded successfully to {output_path}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Error downloading file: {e}[/red]")
            return False
    
    def delete(self, filename: str) -> bool:
        """Delete a file from the backend by filename (prioritizes current directory)"""
        # Show current directory context
        if self.current_folder_name:
            console.print(f"[blue]Deleting from current directory: {self.current_folder_name}[/blue]")
        else:
            console.print(f"[blue]Deleting from root directory[/blue]")
        
        file_id = self.get_file_id_by_name_in_current_dir(filename)
        if not file_id:
            console.print(f"[red]File '{filename}' not found.[/red]")
            return False
        url = f"{self.base_url}/delete/{file_id}"
        try:
            response = self.session.delete(url)
            if response.status_code != 200:
                console.print(f"[red]Delete failed: {response.text}[/red]")
                return False
            console.print(f"[green]File '{filename}' deleted successfully![/green]")
            return True
        except Exception as e:
            console.print(f"[red]Error deleting file: {e}[/red]")
            return False
    
    def logout(self) -> bool:
        """Logout from the Document Server backend"""
        try:
            # Get current user info before logging out
            user_info = self.get_current_user()
            username = user_info.get('username') if user_info else None
            
            # Call backend logout endpoint
            self._make_request('POST', '/logout')
            
            # Clear local session
            self._clear_session()
            
            # Reset current directory to root
            self.current_folder_id = None
            self.current_folder_name = None
            
            # Remove terminal-specific session file
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
        # If no cookies are set, try to auto-load a session
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
        # Check if current session is valid
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
    
    def _find_file_in_tree(self, folder: dict, file_id: int):
        """Recursively find a file in the folder tree by ID."""
        for file in folder.get('files', []):
            if file['id'] == file_id:
                return file
        for child in folder.get('children', []):
            result = self._find_file_in_tree(child, file_id)
            if result:
                return result
        return None
    
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
    
    def delete_folder_by_name(self, folder_name: str) -> bool:
        """Delete a folder by name"""
        if not self.is_session_valid():
            console.print("[yellow]Please login first[/yellow]")
            return False
        
        # Find folder ID by name
        folder_id = self.get_folder_id_by_name(folder_name)
        if not folder_id:
            console.print(f"[red]Folder '{folder_name}' not found[/red]")
            return False
        
        # Delete the folder using its ID
        return self.delete_folder(folder_id)
    
    def delete_folder(self, folder_id: int) -> bool:
        """Delete a folder by ID"""
        if not self.is_session_valid():
            console.print("[yellow]Please login first[/yellow]")
            return False
        
        try:
            response = self._make_request('DELETE', f'/folders/{folder_id}')
            
            if response and response.get('message') == 'Folder deleted successfully':
                console.print(f"[green]Folder deleted successfully![/green]")
                return True
            else:
                error_msg = response.get('error', 'Failed to delete folder') if response else 'Failed to delete folder'
                console.print(f"[red]Failed to delete folder: {error_msg}[/red]")
                return False
        except Exception as e:
            console.print(f"[red]Error deleting folder: {e}[/red]")
            return False
    
    def show_folder_tree(self) -> bool:
        """Show folder tree structure"""
        if not self.is_session_valid():
            console.print("[yellow]Please login first[/yellow]")
            return False
        
        try:
            response = self._make_request('GET', '/folders')
            
            if response and 'tree' in response:
                tree = response['tree']
                self._display_folder_tree(tree)
                return True
            else:
                console.print("[red]Failed to retrieve folder tree[/red]")
                return False
        except Exception as e:
            console.print(f"[red]Error showing folder tree: {e}[/red]")
            return False
    
    def _display_folder_tree(self, folder, level=0):
        """Recursively display folder tree"""
        indent = "  " * level
        if folder.get('id'):
            console.print(f"{indent}📁 {folder['name']} (ID: {folder['id']})")
            
            # Show files in this folder
            for file in folder.get('files', []):
                file_indent = "  " * (level + 1)
                status = "📋" if file.get('is_under_review') else "📄"
                console.print(f"{file_indent}{status} {file['name']}")
            
            # Show subfolders
            for child in folder.get('children', []):
                self._display_folder_tree(child, level + 1)
        else:
            console.print(f"{indent}📁 Root")
    
    def change_directory(self, folder_name: str) -> bool:
        """Change current directory context"""
        if not self.is_session_valid():
            console.print("[yellow]Please login first[/yellow]")
            return False
        
        # Handle special cases
        if folder_name == "/" or folder_name == "root":
            self.current_folder_id = None
            self.current_folder_name = None
            console.print("[green]Changed to root directory[/green]")
            return True
        
        # Find folder ID by name
        folder_id = self.get_folder_id_by_name(folder_name)
        if folder_id:
            self.current_folder_id = folder_id
            self.current_folder_name = folder_name
            console.print(f"[green]Changed to folder: {folder_name}[/green]")
            return True
        else:
            console.print(f"[red]Folder '{folder_name}' not found[/red]")
            return False
    
    def show_current_directory(self) -> bool:
        """Show current directory path"""
        if not self.is_session_valid():
            console.print("[yellow]Please login first[/yellow]")
            return False
        
        if self.current_folder_name:
            console.print(f"[cyan]Current directory: /{self.current_folder_name}[/cyan]")
        else:
            console.print("[cyan]Current directory: / (root)[/cyan]")
        return True
    
    def list_files_in_folder(self, folder_name: str = None) -> bool:
        """List files and folders in a specific folder or current directory"""
        if not self.is_session_valid():
            console.print("[yellow]Please login first[/yellow]")
            return False
        
        try:
            response = self._make_request('GET', '/folders')
            
            if response and 'tree' in response:
                tree = response['tree']
                
                if folder_name:
                    # Find specific folder
                    folder = self._find_folder_in_tree(tree, folder_name)
                    if folder:
                        console.print(f"[cyan]Contents of folder '{folder_name}':[/cyan]")
                        self._display_folder_contents(folder)
                    else:
                        console.print(f"[red]Folder '{folder_name}' not found[/red]")
                        return False
                else:
                    # Use current directory context
                    if self.current_folder_name:
                        folder = self._find_folder_in_tree(tree, self.current_folder_name)
                        if folder:
                            console.print(f"[cyan]Contents of current directory '{self.current_folder_name}':[/cyan]")
                            self._display_folder_contents(folder)
                        else:
                            console.print(f"[red]Current directory '{self.current_folder_name}' not found[/red]")
                            return False
                    else:
                        # Show all files and folders in root
                        console.print("[cyan]Contents of root directory:[/cyan]")
                        self._display_folder_contents(tree)
                
                return True
            else:
                console.print("[red]Failed to retrieve folders[/red]")
                return False
        except Exception as e:
            console.print(f"[red]Error listing files: {e}[/red]")
            return False
    
    def _display_folder_contents(self, folder: Dict[str, Any]):
        """Display files and folders in a folder"""
        items = []
        
        # Add subfolders
        for child in folder.get('children', []):
            items.append({
                'type': 'folder',
                'name': child['name'],
                'id': child['id']
            })
        
        # Add files
        for file in folder.get('files', []):
            items.append({
                'type': 'file',
                'name': file['name'],
                'id': file['id'],
                'status': 'Under Review' if file.get('is_under_review') else 'Available'
            })
        
        if not items:
            console.print("[yellow]No files or folders found[/yellow]")
            return
        
        # Sort items: folders first, then files
        items.sort(key=lambda x: (x['type'] != 'folder', x['name'].lower()))
        
        # Display items
        for item in items:
            if item['type'] == 'folder':
                console.print(f"  📁 {item['name']}/ (ID: {item['id']})")
            else:
                status_icon = "📋" if item['status'] == 'Under Review' else "📄"
                console.print(f"  {status_icon} {item['name']} - {item['status']}")
    
    def _find_folder_in_tree(self, tree, folder_name: str):
        """Find a folder by name in the tree structure"""
        if tree.get('name') == folder_name:
            return tree
        
        for child in tree.get('children', []):
            result = self._find_folder_in_tree(child, folder_name)
            if result:
                return result
        
        return None
    
    def move_file(self, filename: str, folder_name: str) -> bool:
        """Move a file to a different folder"""
        if not self.is_session_valid():
            console.print("[yellow]Please login first[/yellow]")
            return False
        
        try:
            # Get file ID
            file_id = self.get_file_id_by_name(filename)
            if not file_id:
                console.print(f"[red]File '{filename}' not found[/red]")
                return False
            
            # Get folder ID
            folder_id = self.get_folder_id_by_name(folder_name)
            if not folder_id:
                console.print(f"[red]Folder '{folder_name}' not found[/red]")
                return False
            
            # Move the file
            data = {
                'file_id': file_id,
                'target_folder_id': folder_id
            }
            
            response = self._make_request('POST', '/move-file', json=data)
            
            if response and response.get('message') == 'File moved successfully':
                console.print(f"[green]File '{filename}' moved to folder '{folder_name}' successfully![/green]")
                return True
            else:
                error_msg = response.get('error', 'Failed to move file') if response else 'Failed to move file'
                console.print(f"[red]Failed to move file: {error_msg}[/red]")
                return False
        except Exception as e:
            console.print(f"[red]Error moving file: {e}[/red]")
            return False
    
    def list_folders(self) -> bool:
        """List all folders in a flat structure"""
        if not self.is_session_valid():
            console.print("[yellow]Please login first[/yellow]")
            return False
        
        try:
            response = self._make_request('GET', '/folders')
            
            if response and 'flat' in response:
                folders = response['flat']
                
                if not folders:
                    console.print("[yellow]No folders found[/yellow]")
                    return True
                
                table = Table(title="Folders")
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("Name", style="green")
                
                for folder in folders:
                    table.add_row(
                        str(folder['id']),
                        folder['name']
                    )
                
                console.print(table)
                return True
            else:
                console.print("[red]Failed to retrieve folders[/red]")
                return False
        except Exception as e:
            console.print(f"[red]Error listing folders: {e}[/red]")
            return False
    
    def create_folder(self, folder_name: str, parent_id: Optional[int] = None) -> bool:
        """Create a new folder"""
        if not self.is_session_valid():
            console.print("[yellow]Please login first[/yellow]")
            return False
        
        if not folder_name or not folder_name.strip():
            console.print("[red]Folder name cannot be empty[/red]")
            return False
        
        try:
            payload = {'name': folder_name.strip()}
            
            # If no parent_id specified, use current folder
            if parent_id is None:
                if self.current_folder_id is not None:
                    payload['parent_id'] = self.current_folder_id
                    console.print(f"[blue]Creating folder in current directory: {self.current_folder_name}[/blue]")
                # If current_folder_id is None, folder will be created in root (no parent_id)
            else:
                payload['parent_id'] = parent_id
            
            response = self._make_request('POST', '/folders', json=payload)
            
            if response and response.get('message') == 'Folder created':
                folder_id = response.get('folder_id', 'N/A')
                console.print(f"[green]Folder '{folder_name}' created successfully![/green]")
                console.print(f"[blue]Folder ID: {folder_id}[/blue]")
                return True
            else:
                error_msg = response.get('error', 'Failed to create folder') if response else 'Failed to create folder'
                console.print(f"[red]Failed to create folder: {error_msg}[/red]")
                return False
        except Exception as e:
            console.print(f"[red]Error creating folder: {e}[/red]")
            return False
    
    def get_folder_id_by_name(self, folder_name: str) -> Optional[int]:
        """Get folder ID by name (searches entire folder tree)"""
        if not self.is_session_valid():
            console.print("[yellow]Please login first[/yellow]")
            return None
        
        try:
            response = self._make_request('GET', '/folders')
            
            if response and 'tree' in response:
                tree = response['tree']
                
                # Search in the entire tree structure
                def search_folder_in_tree(folder_tree):
                    if folder_tree.get('name') == folder_name:
                        return folder_tree.get('id')
                    
                    # Search in subfolders
                    for child in folder_tree.get('children', []):
                        result = search_folder_in_tree(child)
                        if result:
                            return result
                    
                    return None
                
                return search_folder_in_tree(tree)
            else:
                console.print("[red]Failed to retrieve folders[/red]")
                return None
        except Exception as e:
            console.print(f"[red]Error getting folder ID: {e}[/red]")
            return None 