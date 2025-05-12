from tmdbv3api import TMDb, Movie
import os
import sys

def test_tmdb_search():
    # Initialize TMDb API
    tmdb = TMDb()
    tmdb.api_key = 'b9cc1363ba35084ff7e41934f68bb737'
    tmdb.timeout = 15
    
    # Create movie instance
    movie = Movie()
    
    # Search for movies
    query = 'avatar'
    try:
        search_results = movie.search(query)
        print(f"Search for '{query}' found {len(search_results)} results")
        
        # Print the first few results
        for i, result in enumerate(search_results[:3], 1):
            print(f"Result {i}:")
            print(f"  Title: {result.title if hasattr(result, 'title') else 'Unknown'}")
            print(f"  ID: {result.id if hasattr(result, 'id') else 'Unknown'}")
            print(f"  Release Date: {result.release_date if hasattr(result, 'release_date') else 'Unknown'}")
            print()
        
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing TMDB API search...")
    success = test_tmdb_search()
    print(f"Test {'passed' if success else 'failed'}") 