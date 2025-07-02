"""
Folder operations for Document Server CLI
"""

from typing import Dict, Any, Optional
from rich.console import Console
from rich.table import Table

console = Console()


class FolderManager:
    """Manages folder operations for the CLI"""
    
    def __init__(self, session_manager):
        self.session_manager = session_manager
        self.current_folder_id = None
        self.current_folder_name = None
    
    def create_folder(self, folder_name: str, parent_id: Optional[int] = None) -> bool:
        """Create a new folder"""
        if not self.session_manager.is_session_valid():
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
            else:
                payload['parent_id'] = parent_id
            
            response = self.session_manager._make_request('POST', '/folders', json=payload)
            
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
    
    def delete_folder_by_name(self, folder_name: str) -> bool:
        """Delete a folder by name"""
        if not self.session_manager.is_session_valid():
            console.print("[yellow]Please login first[/yellow]")
            return False
        
        folder_id = self.get_folder_id_by_name(folder_name)
        if not folder_id:
            console.print(f"[red]Folder '{folder_name}' not found[/red]")
            return False
        
        return self.delete_folder(folder_id)
    
    def delete_folder(self, folder_id: int) -> bool:
        """Delete a folder by ID"""
        if not self.session_manager.is_session_valid():
            console.print("[yellow]Please login first[/yellow]")
            return False
        
        try:
            response = self.session_manager._make_request('DELETE', f'/folders/{folder_id}')
            
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
    
    def change_directory(self, folder_name: str) -> bool:
        """Change current directory context"""
        if not self.session_manager.is_session_valid():
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
        if not self.session_manager.is_session_valid():
            console.print("[yellow]Please login first[/yellow]")
            return False
        
        if self.current_folder_name:
            console.print(f"[cyan]Current directory: /{self.current_folder_name}[/cyan]")
        else:
            console.print("[cyan]Current directory: / (root)[/cyan]")
        return True
    
    def list_folders(self) -> bool:
        """List all folders in a flat structure"""
        if not self.session_manager.is_session_valid():
            console.print("[yellow]Please login first[/yellow]")
            return False
        
        try:
            response = self.session_manager._make_request('GET', '/folders')
            
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
    
    def show_folder_tree(self) -> bool:
        """Show folder tree structure"""
        if not self.session_manager.is_session_valid():
            console.print("[yellow]Please login first[/yellow]")
            return False
        
        try:
            response = self.session_manager._make_request('GET', '/folders')
            
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
    
    def list_files_in_folder(self, folder_name: str = None) -> bool:
        """List files and folders in a specific folder or current directory"""
        if not self.session_manager.is_session_valid():
            console.print("[yellow]Please login first[/yellow]")
            return False
        
        try:
            response = self.session_manager._make_request('GET', '/folders')
            
            if response and 'tree' in response:
                tree = response['tree']
                
                if folder_name:
                    folder = self._find_folder_in_tree(tree, folder_name)
                    if folder:
                        console.print(f"[cyan]Contents of folder '{folder_name}':[/cyan]")
                        self._display_folder_contents(folder)
                    else:
                        console.print(f"[red]Folder '{folder_name}' not found[/red]")
                        return False
                else:
                    if self.current_folder_name:
                        folder = self._find_folder_in_tree(tree, self.current_folder_name)
                        if folder:
                            console.print(f"[cyan]Contents of current directory '{self.current_folder_name}':[/cyan]")
                            self._display_folder_contents(folder)
                        else:
                            console.print(f"[red]Current directory '{self.current_folder_name}' not found[/red]")
                            return False
                    else:
                        console.print("[cyan]Contents of root directory:[/cyan]")
                        self._display_folder_contents(tree)
                
                return True
            else:
                console.print("[red]Failed to retrieve folders[/red]")
                return False
        except Exception as e:
            console.print(f"[red]Error listing files: {e}[/red]")
            return False
    
    def move_file(self, filename: str, folder_name: str) -> bool:
        """Move a file to a different folder"""
        if not self.session_manager.is_session_valid():
            console.print("[yellow]Please login first[/yellow]")
            return False
        
        try:
            # Get file ID
            from .files import FileManager
            file_manager = FileManager(self.session_manager)
            file_id = file_manager.get_file_id_by_name(filename)
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
            
            response = self.session_manager._make_request('POST', '/move-file', json=data)
            
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
    
    def get_folder_id_by_name(self, folder_name: str) -> Optional[int]:
        """Get folder ID by name (searches entire folder tree)"""
        if not self.session_manager.is_session_valid():
            console.print("[yellow]Please login first[/yellow]")
            return None
        
        try:
            response = self.session_manager._make_request('GET', '/folders')
            
            if response and 'tree' in response:
                tree = response['tree']
                
                def search_folder_in_tree(folder_tree):
                    if folder_tree.get('name') == folder_name:
                        return folder_tree.get('id')
                    
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