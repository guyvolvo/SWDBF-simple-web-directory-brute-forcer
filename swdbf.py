#!/usr/bin/env python3
# Simple Web Directory Brute Forcer
import requests
import argparse
import sys
import signal
from urllib.parse import urljoin
from colorama import Fore, init
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

init(autoreset=True)
running = True
print_lock = Lock()  # Lock for thread-safe printing


def signal_handler(sig, frame):
    global running
    print("\n[!] Ending session...")
    running = False
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

parser = argparse.ArgumentParser(
    prog='swdbf',
    description='Simple Web Directory Brute Forcer',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog='''
Examples:
  swdbf -u http://example.com -w wordlist.txt
  swdbf -u example.com -p 8080 -w dirs.txt
    ''')

parser.add_argument('-u', '--url', type=str, required=True, help='URL of the target')
parser.add_argument('-p', '--port', type=int, required=False, help='Port of the target')
parser.add_argument('-t', '--timeout', type=int, required=False, default=3, help='Timeout connection')
parser.add_argument('-w', '--wordlist', type=str, required=True, help='What wordlist to use')
parser.add_argument('-T', '--threads', type=int, required=False, default=10, help='Number of threads (default: 10)')
args = parser.parse_args()


def check_directory(url, timeout):
    """Check a single directory - used by threads"""
    global running

    if not running:
        return None
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=False)

        # Check for false positives
        content_lower = response.text.lower()
        is_error = any(keyword in content_lower for keyword in [
            'not found', '404', 'invalid request', 'error',
            'does not exist', 'page not found'
        ])

        if response.status_code == 200 and not is_error:
            size = len(response.content)
            with print_lock:
                print(f"{Fore.GREEN}[+] {response.status_code} - {url} [{size} bytes]")
        elif response.status_code in [301, 302, 307, 308]:
            with print_lock:
                print(f"{Fore.YELLOW}[>] {response.status_code} - {url} -> {response.headers.get('Location', 'N/A')}")
        elif response.status_code == 403:
            with print_lock:
                print(f"{Fore.RED}[!] {response.status_code} - {url} (Forbidden)")

    except requests.exceptions.Timeout:
        with print_lock:
            print(f"[-] Timeout - {url}")
    except requests.exceptions.ConnectionError:
        pass  # Suppress connection errors to reduce noise
    except Exception as e:
        with print_lock:
            print(f"[-] Error - {url}: {str(e)}")

    return None


def brute_force(target, port, wordlist, timeout, threads):
    global running

    # Build base URL with port if provided
    # Only add port if it's explicitly provided by user
    if port:
        # Check if URL already has a port
        if ':' in target.split('://')[-1]:
            base_url = target
        else:
            base_url = f"{target}:{port}"
    else:
        base_url = target

    # Add http:// if no scheme
    if not base_url.startswith(('http://', 'https://')):
        base_url = f"http://{base_url}"

    print(f"[*] Target: {base_url}")
    print(f"[*] Wordlist: {wordlist}")
    print(f"[*] Threads: {threads}")
    print(f"[*] Starting directory enumeration...\n")

    try:
        # Read all directories from wordlist
        with open(wordlist, 'r') as f:
            directories = [line.strip() for line in f if line.strip()]

        print(f"[*] Loaded {len(directories)} entries from wordlist\n")

        # Use ThreadPoolExecutor for concurrent requests
        with ThreadPoolExecutor(max_workers=threads) as executor:
            # Create futures for all directories
            futures = []
            for directory in directories:
                if not running:
                    break
                url = urljoin(base_url, directory)
                future = executor.submit(check_directory, url, timeout)
                futures.append(future)

            # Wait for all futures to complete
            for future in as_completed(futures):
                if not running:
                    break
                future.result()  # This will raise any exceptions that occurred

    # Handling file exceptions
    except FileNotFoundError:
        print(f"[!] Error: wordlist file '{wordlist}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"[!] Error reading wordlist: {str(e)}")
        sys.exit(1)

    if running:
        print("\n[*] Brute force complete!")


if __name__ == "__main__":
    brute_force(args.url, args.port, args.wordlist, args.timeout, args.threads)