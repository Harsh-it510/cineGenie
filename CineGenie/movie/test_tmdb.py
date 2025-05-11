import requests
import json
import sys
import os
import socket
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Set your TMDb API key
API_KEY = "b9cc1363ba35084ff7e41934f68bb737"

# Create a session with retry logic
def create_requests_session(retries=3, backoff_factor=0.3, timeout=15):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=(500, 502, 503, 504),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def test_tmdb_connection():
    print("Testing connection to TMDb API...")
    url = "https://api.themoviedb.org/3/movie/popular"
    params = {"api_key": API_KEY}
    
    # Try with standard requests first
    try:
        print("Trying standard requests...")
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'results' in data and data['results']:
                print("Success with standard requests!")
                return True
            else:
                print("API returned a successful response but no movie data was found.")
        else:
            print(f"Failed with status code: {response.status_code}, message: {response.text}")
    except Exception as e:
        print(f"Error with standard requests: {type(e).__name__}: {str(e)}")
    
    # Try with retry session
    try:
        print("\nTrying with retry session...")
        session = create_requests_session()
        response = session.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if 'results' in data and data['results']:
                print("Success with retry session!")
                movie = data['results'][0]
                print(f"First movie title: {movie.get('title', 'Unknown')}")
                return True
            else:
                print("API returned a successful response but no movie data was found.")
        else:
            print(f"Failed with status code: {response.status_code}, message: {response.text}")
    except Exception as e:
        print(f"Error with retry session: {type(e).__name__}: {str(e)}")
    
    # Try with proxy bypass
    try:
        print("\nTrying direct connection without proxy...")
        # Temporarily disable any proxy settings
        original_http_proxy = os.environ.get('HTTP_PROXY')
        original_https_proxy = os.environ.get('HTTPS_PROXY')
        if original_http_proxy:
            del os.environ['HTTP_PROXY']
        if original_https_proxy:
            del os.environ['HTTPS_PROXY']
        
        session = create_requests_session()
        response = session.get(url, params=params, timeout=20)
        
        # Restore proxy settings
        if original_http_proxy:
            os.environ['HTTP_PROXY'] = original_http_proxy
        if original_https_proxy:
            os.environ['HTTPS_PROXY'] = original_https_proxy
            
        if response.status_code == 200:
            data = response.json()
            if 'results' in data and data['results']:
                print("Success with direct connection!")
                return True
            else:
                print("API returned a successful response but no movie data was found.")
        else:
            print(f"Failed with status code: {response.status_code}, message: {response.text}")
    except Exception as e:
        print(f"Error with direct connection: {type(e).__name__}: {str(e)}")
    
    return False

def print_network_info():
    """Print current network configuration information"""
    print("\nNetwork Information:")
    try:
        hostname = socket.gethostname()
        print(f"Hostname: {hostname}")
        ip = socket.gethostbyname(hostname)
        print(f"IP Address: {ip}")
    except Exception as e:
        print(f"Could not get network info: {e}")
    
    # Check proxy settings
    print("\nProxy Settings:")
    print(f"HTTP_PROXY: {os.environ.get('HTTP_PROXY', 'Not set')}")
    print(f"HTTPS_PROXY: {os.environ.get('HTTPS_PROXY', 'Not set')}")
    print(f"NO_PROXY: {os.environ.get('NO_PROXY', 'Not set')}")
    
    # Test connectivity to common sites
    print("\nGeneral Internet Connectivity:")
    test_sites = ["https://www.google.com", "https://www.themoviedb.org"]
    for site in test_sites:
        try:
            response = requests.get(site, timeout=5)
            print(f"Connection to {site}: Success (Status code: {response.status_code})")
        except Exception as e:
            print(f"Connection to {site}: Failed ({type(e).__name__}: {str(e)})")

if __name__ == "__main__":
    print("TMDb API Connection Test")
    print("=======================")
    
    print_network_info()
    
    print("\nTesting TMDB API Connection:")
    success = test_tmdb_connection()
    
    if success:
        print("\nSUCCESS: TMDb API connection is working properly!")
        sys.exit(0)
    else:
        print("\nFAILED: Could not connect to TMDb API.")
        print("\nTroubleshooting steps:")
        print("1. Check your internet connection")
        print("2. Verify that the API key is correct")
        print("3. Check if there are any firewalls or proxies blocking the connection")
        print("4. Try using a VPN if region restrictions might be in place")
        print("5. Check if the TMDb API is currently having issues: https://status.themoviedb.org/")
        sys.exit(1) 