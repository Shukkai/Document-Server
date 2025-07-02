"""
File operations for Document Server CLI
"""

import os
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional
from io import BytesIO
import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class FileManager:
    """Manages file operations for the CLI"""
    
    def __init__(self, session_manager):
        self.session_manager = session_manager
        self.base_url = session_manager.base_url
        self.session = session_manager.session
    
    def upload(self, file_path: str, current_folder_id: int = None, current_folder_name: str = None) -> bool:
        """Upload a file to the backend"""
        if not self.session_manager.is_session_valid():
            console.print("[yellow]Please login first[/yellow]")
            return False
        
        # Resolve file path with multiple fallback strategies
        original_path = Path(file_path)
        resolved_path = None
        
        search_paths = [
            original_path,
            Path.cwd() / original_path,
            Path.cwd().parent / original_path,
            Path.home() / original_path,
            Path.home() / "Downloads" / original_path,
        ]
        
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
        if current_folder_name:
            console.print(f"[blue]Uploading to current directory: {current_folder_name}[/blue]")
        else:
            console.print(f"[blue]Uploading to root directory[/blue]")
        
        try:
            with open(resolved_path, 'rb') as file_obj:
                file_content = file_obj.read()
            
            mime_type, _ = mimetypes.guess_type(str(resolved_path))
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            files = {'file': (resolved_path.name, BytesIO(file_content), mime_type)}
            
            # Add folder_id to the request if we're in a specific folder
            data = {}
            if current_folder_id is not None:
                data['folder_id'] = current_folder_id
            
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
    
    def download(self, filename: str, output_path: Optional[str] = None) -> bool:
        """Download a file from the backend by filename"""
        if not self.session_manager.is_session_valid():
            console.print("[yellow]Please login first[/yellow]")
            return False
        
        file_id = self.get_file_id_by_name(filename)
        if not file_id:
            console.print(f"[red]File '{filename}' not found.[/red]")
            return False
        
        folders_data = self.session_manager._make_request('GET', '/folders')
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
    
    def delete(self, filename: str, current_folder_name: str = None) -> bool:
        """Delete a file from the backend by filename (prioritizes current directory)"""
        if not self.session_manager.is_session_valid():
            console.print("[yellow]Please login first[/yellow]")
            return False
        
        # Show current directory context
        if current_folder_name:
            console.print(f"[blue]Deleting from current directory: {current_folder_name}[/blue]")
        else:
            console.print(f"[blue]Deleting from root directory[/blue]")
        
        file_id = self.get_file_id_by_name_in_current_dir(filename, current_folder_name)
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
    
    def get_file_id_by_name(self, filename: str) -> Optional[int]:
        """Find file ID by filename for the current user"""
        try:
            response = self.session_manager._make_request('GET', '/folders')
            if not response or 'tree' not in response:
                return None
            
            def search_file_in_tree(tree):
                for file in tree.get('files', []):
                    if file['name'] == filename:
                        return file['id']
                
                for child in tree.get('children', []):
                    result = search_file_in_tree(child)
                    if result:
                        return result
                
                return None
            
            return search_file_in_tree(response['tree'])
        except Exception as e:
            console.print(f"[red]Error finding file: {e}[/red]")
            return None
    
    def get_file_id_by_name_in_current_dir(self, filename: str, current_folder_name: str = None) -> Optional[int]:
        """Find file ID by filename, prioritizing current directory"""
        if not self.session_manager.is_session_valid():
            console.print("[yellow]Please login first[/yellow]")
            return None
        
        try:
            response = self.session_manager._make_request('GET', '/folders')
            if not response or 'tree' not in response:
                return None
            
            tree = response['tree']
            
            # If we're in a specific folder, search there first
            if current_folder_name:
                current_folder = self._find_folder_in_tree(tree, current_folder_name)
                if current_folder:
                    for file in current_folder.get('files', []):
                        if file['name'] == filename:
                            console.print(f"[blue]Found file '{filename}' in current directory: {current_folder_name}[/blue]")
                            return file['id']
            
            # If not found in current directory or we're in root, search entire tree
            def search_file_in_tree(folder_tree):
                for file in folder_tree.get('files', []):
                    if file['name'] == filename:
                        return file['id']
                
                for child in folder_tree.get('children', []):
                    result = search_file_in_tree(child)
                    if result:
                        return result
                
                return None
            
            file_id = search_file_in_tree(tree)
            if file_id and current_folder_name:
                console.print(f"[blue]Found file '{filename}' in different directory[/blue]")
            return file_id
            
        except Exception as e:
            console.print(f"[red]Error finding file: {e}[/red]")
            return None
    
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
    
    def _find_folder_in_tree(self, tree, folder_name: str):
        """Find a folder by name in the tree structure"""
        if tree.get('name') == folder_name:
            return tree
        
        for child in tree.get('children', []):
            result = self._find_folder_in_tree(child, folder_name)
            if result:
                return result
        
        return None 