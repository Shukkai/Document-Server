#!/usr/bin/env python3
"""
Simple Redis CLI tool for testing Redis functionality
"""

import redis
import json
import os
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def test_redis_connection():
    """Test Redis connection"""
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        r = redis.from_url(redis_url, decode_responses=True)
        
        # Test connection
        r.ping()
        console.print("[green]✓ Redis connection successful![/green]")
        
        # Get Redis info
        info = r.info()
        
        table = Table(title="Redis Server Information")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Redis Version", info.get('redis_version', 'Unknown'))
        table.add_row("Used Memory", info.get('used_memory_human', 'Unknown'))
        table.add_row("Connected Clients", str(info.get('connected_clients', 'Unknown')))
        table.add_row("Total Commands", str(info.get('total_commands_processed', 'Unknown')))
        table.add_row("Uptime", f"{info.get('uptime_in_seconds', 0)} seconds")
        
        console.print(table)
        
        return r
        
    except Exception as e:
        console.print(f"[red]✗ Redis connection failed: {e}[/red]")
        return None

def test_basic_operations(r):
    """Test basic Redis operations"""
    console.print("\n[bold]Testing Basic Operations:[/bold]")
    
    # Test SET/GET
    r.set('test_key', 'test_value')
    value = r.get('test_key')
    console.print(f"[green]✓ SET/GET test: {value}[/green]")
    
    # Test JSON serialization
    test_data = {'name': 'test', 'value': 123, 'nested': {'key': 'value'}}
    r.set('test_json', json.dumps(test_data))
    retrieved = json.loads(r.get('test_json'))
    console.print(f"[green]✓ JSON test: {retrieved}[/green]")
    
    # Test expiration
    r.set('test_expire', 'will_expire', ex=5)
    ttl = r.ttl('test_expire')
    console.print(f"[green]✓ Expiration test: TTL = {ttl}s[/green]")
    
    # Cleanup
    r.delete('test_key', 'test_json', 'test_expire')
    console.print("[green]✓ Cleanup completed[/green]")

def show_keys(r):
    """Show all keys in Redis"""
    keys = r.keys('*')
    
    if not keys:
        console.print("[yellow]No keys found in Redis[/yellow]")
        return
    
    table = Table(title=f"Redis Keys ({len(keys)} total)")
    table.add_column("Key", style="cyan")
    table.add_column("Type", style="blue")
    table.add_column("TTL", style="yellow")
    table.add_column("Size", style="green")
    
    for key in sorted(keys):
        key_type = r.type(key)
        ttl = r.ttl(key)
        ttl_str = f"{ttl}s" if ttl > 0 else "No TTL" if ttl == -1 else "Expired"
        
        # Get size based on type
        if key_type == 'string':
            size = len(r.get(key) or '')
        elif key_type == 'list':
            size = r.llen(key)
        elif key_type == 'set':
            size = r.scard(key)
        elif key_type == 'hash':
            size = r.hlen(key)
        else:
            size = 'N/A'
        
        table.add_row(key, key_type, ttl_str, str(size))
    
    console.print(table)

def main():
    """Main CLI interface"""
    console.print(Panel.fit(
        "[bold blue]Redis CLI Tool[/bold blue]\n"
        "[dim]Test Redis functionality and view cache data[/dim]",
        title="Welcome"
    ))
    
    # Test connection
    r = test_redis_connection()
    if not r:
        console.print("[red]Cannot proceed without Redis connection[/red]")
        sys.exit(1)
    
    while True:
        console.print("\n[bold]Available Commands:[/bold]")
        console.print("1. [cyan]test[/cyan] - Test basic operations")
        console.print("2. [cyan]keys[/cyan] - Show all keys")
        console.print("3. [cyan]get <key>[/cyan] - Get a specific key")
        console.print("4. [cyan]set <key> <value>[/cyan] - Set a key")
        console.print("5. [cyan]del <key>[/cyan] - Delete a key")
        console.print("6. [cyan]flush[/cyan] - Clear all keys")
        console.print("7. [cyan]exit[/cyan] - Exit")
        
        try:
            command = input("\n[bold blue]redis-cli[/bold blue]> ").strip()
            
            if not command:
                continue
            
            parts = command.split()
            cmd = parts[0].lower()
            
            if cmd == 'test':
                test_basic_operations(r)
                
            elif cmd == 'keys':
                show_keys(r)
                
            elif cmd == 'get' and len(parts) > 1:
                key = parts[1]
                value = r.get(key)
                if value is not None:
                    try:
                        # Try to parse as JSON
                        parsed = json.loads(value)
                        console.print(f"[green]Value:[/green] {json.dumps(parsed, indent=2)}")
                    except:
                        console.print(f"[green]Value:[/green] {value}")
                else:
                    console.print(f"[yellow]Key '{key}' not found[/yellow]")
                    
            elif cmd == 'set' and len(parts) > 2:
                key = parts[1]
                value = ' '.join(parts[2:])
                r.set(key, value)
                console.print(f"[green]Set key '{key}' to '{value}'[/green]")
                
            elif cmd == 'del' and len(parts) > 1:
                key = parts[1]
                deleted = r.delete(key)
                if deleted:
                    console.print(f"[green]Deleted key '{key}'[/green]")
                else:
                    console.print(f"[yellow]Key '{key}' not found[/yellow]")
                    
            elif cmd == 'flush':
                confirm = input("Are you sure you want to clear all keys? (y/N): ")
                if confirm.lower() == 'y':
                    r.flushall()
                    console.print("[green]All keys cleared[/green]")
                else:
                    console.print("[yellow]Operation cancelled[/yellow]")
                    
            elif cmd in ['exit', 'quit']:
                console.print("[green]Goodbye![/green]")
                break
                
            else:
                console.print("[red]Unknown command or missing arguments[/red]")
                
        except KeyboardInterrupt:
            console.print("\n[green]Goodbye![/green]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    main() 