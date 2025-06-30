"""
Document Server CLI Commands
"""

import sys
import click
from .client import DocumentServerCLI
from rich.console import Console

console = Console()


@click.group()
@click.option('--url', default=None, help='Document Server Backend URL')
@click.pass_context
def cli(ctx, url):
    """Document Server CLI"""
    ctx.ensure_object(dict)
    ctx.obj['cli'] = DocumentServerCLI(url)


@cli.command()
@click.argument('username')
@click.option('--password', prompt=sys.stdin.isatty(), hide_input=True, help='User password')
@click.pass_context
def login(ctx, username, password):
    """Login to the Document Server backend"""
    cli_instance = ctx.obj['cli']
    if not cli_instance.login(username, password):
        sys.exit(1)


@cli.command()
@click.argument('username')
@click.argument('email')
@click.option('--password', prompt=sys.stdin.isatty(), hide_input=True, help='User password')
@click.option('--grade', default=33, type=int, help='User grade (default: 33)')
@click.pass_context
def register(ctx, username, email, password, grade):
    """Register a new user account"""
    cli_instance = ctx.obj['cli']
    if not cli_instance.register(username, email, password, grade):
        sys.exit(1)


@cli.command()
@click.pass_context
def logout(ctx):
    """Logout from the Document Server backend"""
    cli_instance = ctx.obj['cli']
    if not cli_instance.logout():
        sys.exit(1)


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.pass_context
def upload(ctx, file_path):
    """Upload a file to the backend"""
    cli_instance = ctx.obj['cli']
    if not cli_instance.upload(file_path):
        sys.exit(1)


@cli.command()
@click.argument('filename')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.pass_context
def download(ctx, filename, output):
    """Download a file from the backend by filename"""
    cli_instance = ctx.obj['cli']
    if not cli_instance.download(filename, output):
        sys.exit(1)


@cli.command()
@click.pass_context
def list(ctx):
    """List all files from the backend"""
    cli_instance = ctx.obj['cli']
    if not cli_instance.list_files():
        sys.exit(1)


@cli.command()
@click.argument('filename')
@click.pass_context
def delete(ctx, filename):
    """Delete a file from the backend by filename"""
    cli_instance = ctx.obj['cli']
    if not cli_instance.delete(filename):
        sys.exit(1)


@cli.command()
@click.pass_context
def status(ctx):
    """Show current login status"""
    cli_instance = ctx.obj['cli']
    cli_instance.show_login_status()


@cli.command()
@click.pass_context
def list_sessions(ctx):
    """List all available user sessions"""
    cli_instance = ctx.obj['cli']
    sessions = cli_instance.list_sessions()
    
    if not sessions:
        console.print("[yellow]No sessions found[/yellow]")
        return
    
    from rich.table import Table
    table = Table(title="Available Sessions")
    table.add_column("Username", style="cyan")
    table.add_column("Last Active", style="green")
    table.add_column("Status", style="yellow")
    
    for session in sessions:
        # Check if this session is currently active
        cli_instance._load_session_for_user(session['username'])
        is_valid = cli_instance.is_session_valid()
        status = "Active" if is_valid else "Expired"
        
        table.add_row(
            session['username'],
            session['timestamp'],
            status
        )
    
    console.print(table)


@cli.command()
@click.argument('username')
@click.pass_context
def switch_user(ctx, username):
    """Switch to a different user session"""
    cli_instance = ctx.obj['cli']
    if not cli_instance.switch_user(username):
        sys.exit(1) 