#!/usr/bin/env python3
"""
Document Server CLI - Terminal-based Session Management
Each terminal maintains its own independent session, allowing multiple users
to be logged in simultaneously in different terminal windows.
"""

import sys
import signal
import os
from pathlib import Path

# Add the cli directory to the Python path
cli_dir = Path(__file__).parent
sys.path.insert(0, str(cli_dir))

from core.client import DocumentServerCLI
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

def signal_handler(signum, frame):
    """Handle termination signals gracefully"""
    console.print("\n[yellow]Received termination signal. Cleaning up...[/yellow]")
    # Reset current directory to root
    if 'client' in globals():
        client.folder_manager.current_folder_id = None
        client.folder_manager.current_folder_name = None
        console.print("[blue]Current directory reset to root[/blue]")
    sys.exit(0)

def show_welcome():
    """Show welcome message with terminal session info"""
    welcome_text = Text()
    welcome_text.append("Document Server CLI\n", style="bold blue")
    welcome_text.append("Terminal-based Session Management\n", style="cyan")
    welcome_text.append("\nEach terminal maintains its own independent session.\n", style="yellow")
    welcome_text.append("Multiple users can be logged in simultaneously in different terminals.\n", style="yellow")
    
    panel = Panel(welcome_text, title="Welcome", border_style="blue")
    console.print(panel)

def show_help():
    """Show help information"""
    help_text = """
[bold]Available Commands:[/bold]

[green]Authentication:[/green]
  login <username> <password>     - Login to the system
  register <username> <email> <password> [grade] - Register new account
  logout                          - Logout from current session
  status                          - Show current login status

[green]File Operations:[/green]
  upload <file_path>              - Upload a file (to current directory by default)
  list [folder_name]              - List all files or files in specific folder
  download <filename> [output]    - Download a file
  delete <filename>               - Delete a file (from current directory by default)

[green]Folder Operations:[/green]
  mkdir <folder_name> [parent_id] - Create a new folder (in current directory by default)
  folders                         - List all folders
  rmdir <folder_name>             - Delete a folder by name
  tree                            - Show folder tree structure
  cd <folder_name>                - Change current folder context
  pwd                             - Show current folder path
  ls [folder_name]                - List files and folders in specific folder (alias for list)
  mv <filename> <folder_name>     - Move file to different folder

[green]Session Management:[/green]
  sessions                        - List all terminal sessions
  help                            - Show this help message
  exit                            - Exit the CLI

[green]Examples:[/green]
  login admin password123
  mkdir documents
  upload /path/to/document.pdf
  mv document.pdf documents/
  list
  download document.pdf
  logout

[bold]Terminal Session Info:[/bold]
• Each terminal window has its own independent session
• Sessions are automatically saved and restored per terminal
• Multiple users can be logged in simultaneously
• Use 'sessions' to see all active terminal sessions
"""
    console.print(help_text)

def main():
    """Main CLI interface"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize client
    global client
    client = DocumentServerCLI()
    
    # Show welcome message
    show_welcome()
    
    # Show current status
    client.show_login_status()
    
    # Interactive mode
    while True:
        try:
            # Get current user info for prompt
            user_info = client.get_current_user()
            if user_info:
                username = user_info['username']
                console.print(f"\n[bold blue]doccli[/bold blue] ([green]{username}[/green])> ", end="")
            else:
                console.print(f"\n[bold blue]doccli[/bold blue] ([yellow]not logged in[/yellow])> ", end="")
            
            # Get command input
            command = input().strip()
            
            if not command:
                continue
            
            # Parse command
            parts = command.split()
            cmd = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []
            
            # Handle commands
            if cmd == 'login':
                if len(args) < 2:
                    console.print("[red]Usage: login <username> <password>[/red]")
                    continue
                username, password = args[0], args[1]
                client.login(username, password)
                
            elif cmd == 'register':
                if len(args) < 3:
                    console.print("[red]Usage: register <username> <email> <password> [grade][/red]")
                    continue
                username, email, password = args[0], args[1], args[2]
                grade = int(args[3]) if len(args) > 3 else 33
                client.register(username, email, password, grade)
                
            elif cmd == 'logout':
                client.logout()
                
            elif cmd == 'status':
                client.show_login_status()
                
            elif cmd == 'upload':
                if len(args) < 1:
                    console.print("[red]Usage: upload <file_path>[/red]")
                    continue
                file_path = args[0]
                client.upload(file_path)
                
            elif cmd == 'list':
                folder_name = args[0] if len(args) > 0 else None
                client.list_files_in_folder(folder_name)
                
            elif cmd == 'download':
                if len(args) < 1:
                    console.print("[red]Usage: download <filename> [output_path][/red]")
                    continue
                filename = args[0]
                output_path = args[1] if len(args) > 1 else None
                client.download(filename, output_path)
                
            elif cmd == 'delete':
                if len(args) < 1:
                    console.print("[red]Usage: delete <filename>[/red]")
                    continue
                filename = args[0]
                client.delete(filename)
                
            elif cmd == 'mkdir':
                if len(args) < 1:
                    console.print("[red]Usage: mkdir <folder_name> [parent_folder_id][/red]")
                    continue
                folder_name = args[0]
                parent_id = int(args[1]) if len(args) > 1 else None
                client.create_folder(folder_name, parent_id)
                
            elif cmd == 'folders':
                client.list_folders()
                
            elif cmd == 'rmdir':
                if len(args) < 1:
                    console.print("[red]Usage: rmdir <folder_name>[/red]")
                    continue
                folder_name = args[0]
                client.delete_folder_by_name(folder_name)
                
            elif cmd == 'tree':
                client.show_folder_tree()
                
            elif cmd == 'cd':
                if len(args) < 1:
                    console.print("[red]Usage: cd <folder_name>[/red]")
                    continue
                folder_name = args[0]
                client.change_directory(folder_name)
                
            elif cmd == 'pwd':
                client.show_current_directory()
                
            elif cmd == 'ls':
                folder_name = args[0] if len(args) > 0 else None
                client.list_files_in_folder(folder_name)
                
            elif cmd == 'mv':
                if len(args) < 2:
                    console.print("[red]Usage: mv <filename> <folder_name>[/red]")
                    continue
                filename = args[0]
                folder_name = args[1]
                client.move_file(filename, folder_name)
                
            elif cmd == 'sessions':
                sessions = client.list_sessions()
                if not sessions:
                    console.print("[yellow]No active terminal sessions found[/yellow]")
                else:
                    console.print(f"[cyan]Active Terminal Sessions ({len(sessions)}):[/cyan]")
                    for session in sessions:
                        console.print(f"  • {session['username']} (Terminal: {session['session_id']}, PID: {session['process_id']})")
                        console.print(f"    Last active: {session['timestamp']}")
                        console.print()
                
            elif cmd in ['help', '?']:
                show_help()
                
            elif cmd in ['exit', 'quit']:
                # Reset current directory to root before exiting
                client.folder_manager.current_folder_id = None
                client.folder_manager.current_folder_name = None
                console.print("[blue]Current directory reset to root[/blue]")
                console.print("[green]Goodbye![/green]")
                break
                
            else:
                console.print(f"[red]Unknown command: {cmd}[/red]")
                console.print("[yellow]Type 'help' for available commands[/yellow]")
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Use 'exit' to quit the CLI[/yellow]")
        except EOFError:
            console.print("\n[green]Goodbye![/green]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    main() 